"""Build the cited working paper, automatic lists and source-linked code excerpts."""
from pathlib import Path
import inspect
import json
import hashlib
import sys
import textwrap
import re
from xml.sax.saxutils import escape
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from PIL import Image as PILImage
from reportlab.lib import colors
from reportlab.lib.enums import TA_JUSTIFY, TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import BaseDocTemplate, PageTemplate, Frame, Paragraph, Spacer, PageBreak, Table, TableStyle, Image, KeepTogether, XPreformatted
from reportlab.platypus.tableofcontents import TableOfContents

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from market_neutral.historical import baseline_decisions, phase_inputs
from market_neutral.portfolio import neutral_weights
from market_neutral.backtest import execute_targets
from market_neutral.comparison import match_gross_exposure
from market_neutral.inference import stationary_indices, hac_mean_interval
from market_neutral.strategy import build_decisions
from graph_comparison_section import add_graph_comparison

OUT=ROOT/'paper/output'
OUT.mkdir(parents=True,exist_ok=True)
WIDTH=A4[0]-108
FONTROOT=Path(matplotlib.get_data_path())/'fonts/ttf'
for name,file in [('Body','DejaVuSerif.ttf'),('BodyBold','DejaVuSerif-Bold.ttf'),('BodyItalic','DejaVuSerif-Italic.ttf'),('Sans','DejaVuSans.ttf'),('SansBold','DejaVuSans-Bold.ttf'),('Mono','DejaVuSansMono.ttf')]:
    pdfmetrics.registerFont(TTFont(name,str(FONTROOT/file)))
pdfmetrics.registerFontFamily('Body',normal='Body',bold='BodyBold',italic='BodyItalic',boldItalic='BodyBold')
ST=getSampleStyleSheet()
ST.add(ParagraphStyle(name='Text',fontName='Body',fontSize=10.2,leading=15.4,alignment=TA_JUSTIFY,spaceAfter=9))
ST.add(ParagraphStyle(name='Head',fontName='SansBold',fontSize=16,leading=21,spaceAfter=13,textColor=colors.HexColor('#203D4A'),keepWithNext=True))
ST.add(ParagraphStyle(name='Sub',fontName='SansBold',fontSize=11.5,leading=17,spaceBefore=11,spaceAfter=7,keepWithNext=True))
ST.add(ParagraphStyle(name='SmallText',fontName='Body',fontSize=8.6,leading=12.2,spaceAfter=6))
ST.add(ParagraphStyle(name='CaptionText',fontName='Sans',fontSize=8.8,leading=12.3,spaceBefore=6,spaceAfter=8,textColor=colors.HexColor('#375766')))
ST.add(ParagraphStyle(name='Cell',fontName='Sans',fontSize=8.4,leading=11.4))
ST.add(ParagraphStyle(name='TitleText',fontName='SansBold',fontSize=29,leading=36,textColor=colors.HexColor('#203D4A'),spaceAfter=22))
ST.add(ParagraphStyle(name='CodeText',fontName='Mono',fontSize=7.3,leading=10.3,textColor=colors.HexColor('#16343B'),leftIndent=7,rightIndent=7,spaceAfter=5))
refs=json.loads((ROOT/'paper/references.json').read_text())
summary=pd.read_csv(ROOT/'outputs/historical/baseline-summary.csv')
audit=pd.read_csv(ROOT/'outputs/historical/data-audit.csv')
protocol=json.loads((ROOT/'protocol/historical-v1.json').read_text())
comparison=pd.read_csv(ROOT/'outputs/comparison/comparison-summary.csv')
uncertainty=pd.read_csv(ROOT/'outputs/comparison/paired-uncertainty.csv')
graph_default=comparison[(comparison.model=='graph_tau_1')&(comparison.trading_cost_bps==5)&(comparison.annual_borrow_rate==.02)].set_index('phase')
validation_interval=uncertainty[(uncertainty.phase=='validation')&(uncertainty.method=='stationary bootstrap')&(uncertainty.block_or_lags==10)].iloc[0]
default=summary[summary.trading_cost_bps==5].set_index('phase')
story=[];md=[];registrations=[];counts={'Table':0,'Figure':0,'Equation':0,'Listing':0}


class ListOf(TableOfContents):
    def __init__(self,event):
        super().__init__();self.event=event
        self.levelStyles=[ParagraphStyle(name='ListStyle'+event,fontName='Sans',fontSize=8.7,leading=12,spaceBefore=3,leftIndent=0,firstLineIndent=0),
                          ParagraphStyle(name='SubListStyle'+event,fontName='Sans',fontSize=8.7,leading=12,spaceBefore=2,leftIndent=12,firstLineIndent=0)]
        self.tableStyle=TableStyle([('LEFTPADDING',(0,0),(-1,-1),0),('RIGHTPADDING',(0,0),(-1,-1),0),
                                   ('TOPPADDING',(0,0),(-1,-1),0),('BOTTOMPADDING',(0,0),(-1,-1),2)])
    def notify(self,kind,stuff):
        if kind==self.event:super().notify('TOCEntry',stuff)


class Paper(BaseDocTemplate):
    def afterFlowable(self,flowable):
        if hasattr(flowable,'entry'):
            kind,text,key=flowable.entry
            self.canv.bookmarkPage(key)
            level=getattr(flowable,'outline_level',0)
            self.notify(kind,(level,text,self.page,key))
            if kind=='MainTOC':self.canv.addOutlineEntry(text,key,level=level)


def page(canvas,doc):
    if doc.page==1:return
    canvas.saveState();canvas.setStrokeColor(colors.HexColor('#B4C8CF'))
    canvas.line(54,A4[1]-42,A4[0]-54,A4[1]-42)
    canvas.setFont('Sans',8);canvas.setFillColor(colors.HexColor('#536D77'))
    canvas.drawString(54,A4[1]-32,'JOEL CERRAGA  |  MARKET-NEUTRAL TRADING ALGORITHM')
    canvas.drawString(54,30,'Milestone 3 working paper  |  21 September 2026')
    canvas.drawRightString(A4[0]-54,30,str(doc.page));canvas.restoreState()


def p(text,style='Text'):
    story.append(Paragraph(text,ST[style]));md.append(text.replace('<b>','**').replace('</b>','**').replace('<i>','*').replace('</i>','*'))


def heading(text,newpage=False,sub=False):
    if newpage:story.append(PageBreak())
    block=Paragraph(text,ST['Sub' if sub else 'Head'])
    key='section-'+str(len(registrations));block.entry=('MainTOC',text,key);registrations.append(text)
    block.outline_level=1 if re.match(r'^\d+\.\d+\.',text) else 0
    story.append(block);md.append(('### ' if sub else '## ')+text)


def caption(kind,title,keep=False):
    counts[kind]+=1;num=counts[kind];label=f'{kind} {num}. {title}'
    block=Paragraph(label,ST['CaptionText'])
    if keep:block.keepWithNext=True
    block.entry=(kind+'List',label,f'{kind.lower()}-{num}')
    return block,label


def table(title,rows,widths):
    cap,label=caption('Table',title,True);story.append(cap)
    data=[[Paragraph(escape(str(c)),ST['Cell']) for c in row] for row in rows]
    t=Table(data,colWidths=[WIDTH*w for w in widths],repeatRows=1,hAlign='LEFT')
    t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#E5EFF2')),('VALIGN',(0,0),(-1,-1),'TOP'),('BOTTOMPADDING',(0,0),(-1,-1),7),('TOPPADDING',(0,0),(-1,-1),7),('LINEBELOW',(0,0),(-1,0),.7,colors.HexColor('#71939F')),('LINEBELOW',(0,1),(-1,-1),.3,colors.HexColor('#D9E3E6')),('LEFTPADDING',(0,0),(-1,-1),7),('RIGHTPADDING',(0,0),(-1,-1),7)]))
    story.extend([t,Spacer(1,10)])
    markdown_rows=['| '+' | '.join(map(str,r))+' |' for r in rows]
    markdown_rows.insert(1,'| '+' | '.join('---' for _ in rows[0])+' |')
    md.extend([label,'\n'.join(markdown_rows)])


def equation(title,tex,explain):
    number=counts['Equation']+1
    path=OUT/f'equation-{number:02d}.png'
    fig=plt.figure(figsize=(7.1,.65));fig.text(.5,.5,'$'+tex+'$',ha='center',va='center',fontsize=15)
    fig.savefig(path,dpi=300,bbox_inches='tight',pad_inches=.05,transparent=True);plt.close(fig)
    width,height=PILImage.open(path).size
    image=Image(str(path),width=min(WIDTH-85,width/3),height=height/3*min(1,(WIDTH-85)/(width/3)))
    cap,label=caption('Equation',title)
    eqtable=Table([[image,Paragraph(f'Equation {number}',ST['SmallText'])]],colWidths=[WIDTH-80,80])
    eqtable.setStyle(TableStyle([('VALIGN',(0,0),(-1,-1),'MIDDLE'),('ALIGN',(1,0),(1,0),'RIGHT')]))
    eqtable.entry=('EquationList',label,f'equation-{number}')
    story.append(KeepTogether([eqtable,Spacer(1,6),Paragraph(explain,ST['Text'])]))
    md.extend([label,'$$'+tex+f' \\qquad ({number})'+'$$',explain])


def figure(title,path,height=None):
    width,pixels_h=PILImage.open(path).size
    h=WIDTH*pixels_h/width
    if height and h>height:
        w=WIDTH*height/h;h=height
    else:w=WIDTH
    img=Image(str(path),width=w,height=h)
    cap,label=caption('Figure',title)
    story.append(KeepTogether([img,cap]));md.append(f'![{label}](../{Path(path).relative_to(ROOT)})')


def listing(title,fn,start,end):
    source=inspect.getsource(fn);fragment=source[source.index(start):source.index(end)]
    fragment=textwrap.dedent(fragment).strip()
    cap,label=caption('Listing',title,True)
    block=XPreformatted(escape(fragment),ST['CodeText'])
    box=Table([[block]],colWidths=[WIDTH]);box.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,-1),colors.HexColor('#F0F5F6')),('BOX',(0,0),(-1,-1),.4,colors.HexColor('#CCDCE1')),('TOPPADDING',(0,0),(-1,-1),8),('BOTTOMPADDING',(0,0),(-1,-1),8)]))
    story.append(KeepTogether([cap,box]))
    relative=Path(inspect.getsourcefile(fn)).relative_to(ROOT)
    p(f'Source: <b>{relative}</b>, function <b>{fn.__name__}</b>. Selected executable lines; surrounding input checks remain in the module.','SmallText')
    md.extend([label,'```python\n'+fragment+'\n```'])


story.extend([Spacer(1,85),Paragraph('Market-Neutral<br/>Trading Algorithm',ST['TitleText'])])
p('Historical graph comparison, statistical uncertainty and reproducible research','Head')
story.append(Spacer(1,40));p('<b>Joel Cerraga</b>');p('Quant Projects<br/>Milestone 3 working paper<br/>21 September 2026')
story.append(Spacer(1,62));p('Research question','Sub')
p('Can relationships between stock returns improve a constrained reversal strategy after trading costs, borrowing costs and market exposure are accounted for?')
p('This version evaluates the historical graph candidate against the baseline. Persistent homology and the final holdout remain subsequent milestones.','SmallText')

heading('Abstract',True)
d=default.loc['development'];v=default.loc['validation']
p('This project develops a Python framework for a market-neutral equity trading study. A baseline reversal signal is constructed from recent volatility-scaled returns, and portfolios are constrained to approximately zero dollar exposure and zero exposure to estimated market beta. A weighted correlation graph and Laplacian diffusion provide the proposed extension. The present milestone moves from synthetic verification to an exploratory historical study of 24 surviving US companies, with SPY as the benchmark.')
p(f'The acquired dataset contains 2,768 aligned sessions from 2 January 2009 to 31 December 2019. The year 2009 supplies estimation history; 2010-2016 is the development period and 2017-2019 is validation. The final period, 2020-2025, has not been acquired or evaluated. At 5 basis points per dollar traded and 2% annual short borrow, the baseline produces annualised net returns of {d.annualised_return:.2%} in development and {v.annualised_return:.2%} in validation. The corresponding maximum drawdowns are {d.maximum_drawdown:.2%} and {v.maximum_drawdown:.2%}.')
p(f'The fixed graph candidate returns {graph_default.loc["development","annualised_return"]:.2%} annualised in development and {graph_default.loc["validation","annualised_return"]:.2%} in validation. Its validation CAGR improvement over the baseline is {100*(graph_default.loc["validation","annualised_return"]-v.annualised_return):.2f} percentage points, but the 95% stationary-bootstrap interval for the annualised arithmetic daily-return difference spans {100*validation_interval.annualised_lower:+.2f} to {100*validation_interval.annualised_upper:+.2f} percentage points. Both primary strategies remain unprofitable under the stated costs. Forty-four predeclared backtests cover fees, diffusion time, borrow and matched-gross controls; no new primary model is selected.')
p('Current-vintage adjusted data and a fixed survivor basket limit generalisation. The paper records source-linked code, numbered equations, author-led references and reproducible interactive graph explanations. The next milestone will examine topological descriptors against simpler controls while retaining the reserved final period.')

p('<b>Keywords:</b> statistical arbitrage; market neutrality; graph Laplacian; diffusion; historical backtesting; reproducibility.','SmallText')

heading('Table of contents',True);story.append(ListOf('MainTOC'))
heading('List of tables and figures',True)
p('Tables','Sub');story.append(ListOf('TableList'));story.append(Spacer(1,12));p('Figures','Sub');story.append(ListOf('FigureList'))
heading('List of equations and code listings',True)
p('Equations','Sub');story.append(ListOf('EquationList'));story.append(Spacer(1,10));p('Code listings','Sub');story.append(ListOf('ListingList'))
heading('List of abbreviations',True)
table('Abbreviations used in the working paper',[
 ['Abbreviation','Meaning'],['ACT/365','Actual calendar days divided by 365'],['bps','Basis points; one basis point equals 0.01%'],['CAGR','Compound annual growth rate'],['CI','Confidence interval'],['CAPM','Capital Asset Pricing Model'],['CRSP','Center for Research in Security Prices'],['CSCV','Combinatorially symmetric cross-validation'],['CSV','Comma-separated values'],['ETF','Exchange-traded fund'],['H0 / H1','Homology dimensions zero and one'],['HAC','Heteroskedasticity and autocorrelation consistent'],['NAV','Net asset value'],['OLS','Ordinary least squares'],['P&L','Profit and loss'],['PBO','Probability of backtest overfitting'],['pp','Percentage points'],['SB','Stationary bootstrap'],['PCA','Principal component analysis'],['SHA-256','Secure Hash Algorithm, 256-bit digest'],['SPY','Ticker used for the S&P 500 ETF benchmark'],['TDA','Topological data analysis'],['USD','US dollars']],[.22,.78])
heading('List of mathematical symbols',True)
table('Mathematical symbols and definitions',[
 ['Symbol','Definition'],['i, j; t; n','Asset indices; session index; number of assets'],['P; r','Input adjusted price; simple holding-period return'],['h; σ̂','Signal horizon; estimated daily return standard deviation'],['x; s','Volatility-scaled shock; unnormalised trading score'],['β; β̂','Market sensitivity; its trailing estimate'],['A; A⁺','Exposure matrix; Moore-Penrose pseudoinverse'],['q; w','Projected score; portfolio weights relative to post-cost NAV'],['G; b','Maximum gross exposure; maximum absolute name weight'],['ρ; W; D','Pairwise correlation; adjacency matrix; degree matrix'],['d̄; L; τ','Mean weighted degree; scaled Laplacian; diffusion time'],['x̃; d(i,j)','Diffused signal; correlation-derived distance'],['v; V; c','Signed asset notional; NAV; cost per dollar traded'],['a; Δ','Annual borrow rate; elapsed calendar days'],['B; C','Borrow cost; transaction cost'],['R; S; DD','Portfolio return; descriptive Sharpe statistic; drawdown'],['G*; B; G','Common gross exposure; baseline/graph superscript labels'],['δ; μ; T','Paired daily difference; annualised arithmetic mean; phase sample size'],['ℓ; I*','Expected bootstrap block length; resampled observation index'],['K; γ; Ω','HAC lag count; lagged covariance; long-run variance'],['SE; λ','Standard error; graph-Laplacian eigenvalue']],[.27,.73])

heading('1. Introduction and research context',True)
p('As Avellaneda and Lee explain in <i>Statistical arbitrage in the US equities market</i> (2010), systematic equity strategies can use factor-adjusted residual behaviour to form market-neutral portfolios [1]. Their PCA- and ETF-based construction provides context for this research. The present baseline and graph residual are different models, and no result from their paper is transferred to this stock basket.')
p('Lo and MacKinlay, in <i>When Are Contrarian Profits Due to Stock Market Overreaction?</i> (1990), show that contrarian profits need not arise solely from overreaction [2]. This distinction is relevant because reversing a recent stock movement is a trading hypothesis, not proof that its price is incorrect. Accordingly, the first historical experiment retains a simple baseline and evaluates its costs and exposures before adding graph complexity.')
p('The project builds on the earlier SPX density study in its use of controlled numerical checks, reusable Python modules and explanatory notebooks. Its empirical objective is different: it evaluates a trading rule rather than recovering an option-implied probability density. The final research presentation will include a reproducible GitHub repository and an interactive companion page suitable for sharing through LinkedIn.')
heading('1.1. Questions and scope',sub=True)
p('Three questions guide the work. First, does the baseline remain viable after explicit costs? Second, does graph diffusion add information under an otherwise identical experiment? Third, can persistent-homology features add useful regime information beyond simpler measures such as volatility and mean correlation? Milestones 2 and 3 evaluate the first two questions. Persistent homology remains a planned extension.')
p('The experimental code and the scientific references have separate roles. The references justify established concepts and numerical relationships; parameter settings, the fixed basket and the proposed graph score are choices made for this project. The historical comparison below assesses the fixed graph candidate without claiming that its parameter values are justified by the references.')

heading('2. Historical data and experimental protocol',True)
table('Declared equity universe; research groups are not historical index classifications',[['Research group','Stock tickers']]+[[k,', '.join(v)] for k,v in protocol['groups'].items()],[.30,.70])
p('The primary observations are Yahoo Finance daily chart responses [15]. The analysis uses the supplied <b>adjclose</b> field; close, volume, dividend events and split events are retained for audit. The data are current-vintage vendor observations rather than a point-in-time archive. Historical adjustment accuracy has not been independently certified, and dividends are not added a second time to adjusted-price returns.')
table('Chronological allocation fixed before baseline performance was inspected',[
 ['Period','Dates','Use'],['Warm-up','2009','Trailing estimates only'],['Development','2010-2016','Baseline construction and diagnostic evaluation'],['Validation','2017-2019','Declared chronological check; not a final test'],['Final holdout','2020-2025','Reserved; no bars acquired or strategy results inspected in this milestone']],[.22,.22,.56])
p('As White explains in <i>A Reality Check for Data Snooping</i> (2000), repeated model selection on the same observations can create apparently favourable findings by chance [9]. Therefore, the universe, dates, cost scenarios and baseline settings were written to a local protocol and hashed before the equity study was run. This record is not external preregistration, and it does not eliminate knowledge of historical market events.')

heading('2.1. Data audit and sample limitations',True)
table('Data audit for 24 stocks and the SPY benchmark',[
 ['Audit item','Observed result'],['Sessions per series',str(int(audit.rows.min()))],['First / last session','2 January 2009 / 31 December 2019'],['Exact calendar agreement','All 25 series match SPY observations'],['Missing values',str(int(audit['missing'].sum()))],['Nonpositive volume',str(int(audit.nonpositive_volume.sum()))],['Absolute adjusted returns above 40%',str(int(audit.moves_above_40pct.sum()))],['Longest unchanged-price run',str(int(audit.max_unchanged_run.max()))+' sessions'],['Dividend / split events',f'{int(audit.dividend_events.sum())} / {int(audit.split_events.sum())} retained provider events'],['Final holdout','Absent from the permitted historical cache']],[.47,.53])
p('Shumway, in <i>The Delisting Bias in CRSP Data</i> (1997), documents the importance of omitted adverse delisting returns [5]. This project has a broader selection limitation: its named basket contains companies that survived to the selection date. It is consequently an exploratory fixed-basket study and cannot establish performance for the historical investable equity universe.')
p('The loader does not silently forward-fill missing prices or intersect mismatched calendars. Positive prices and reported volumes are required throughout. A 20-session close-times-volume proxy is reported, but this is not a calibrated capacity limit. Borrow availability, suspended securities and a complete corporate-action reconstruction remain unresolved for a production equity simulator.')
equation('Simple adjusted-price return',r'r_{i,t}=\frac{P_{i,t}}{P_{i,t-1}}-1',
 'Equation 1 defines the input return. Where: P is the supplied adjusted-price series, i denotes the asset and t denotes the observed session. Avellaneda and Lee also formulate their historical return analysis using dividend-adjusted prices [1]. Here the resulting return-bearing notionals are an approximation; the ledger does not model raw execution prices and dividend cash flows separately.')

heading('3. Baseline signal and market sensitivity',True)
table('Baseline settings retained from the synthetic prototype',[
 ['Setting','Value'],['Recent-movement horizon','5 sessions'],['Volatility estimate','63 sessions; sample standard deviation'],['Market beta / correlation window','126 sessions'],['Shock clipping','-5 to +5 scaling units'],['Gross / name exposure ceilings','100% / 8% of post-cost NAV'],['Base trading cost','5 bps per dollar bought or sold'],['Alternative trading costs','0, 10 and 20 bps'],['Annual short borrow','2%, ACT/365'],['Initial capital per phase','USD 100,000'],['Execution','Decision at t; trade at t+1 close; first new-position P&L at t+2']],[.48,.52])
equation('Volatility-scaled recent movement',r'x_{i,t}=\operatorname{clip}\left(\frac{\sum_{u=t-h+1}^{t}\log(1+r_{i,u})}{\widehat{\sigma}_{i,t}\sqrt{h}},-5,5\right)',
 'Equation 2 scales recent movement by trailing volatility. Where: h = 5 and sigma-hat is the 63-session daily sample standard deviation. This is a project scaling rule, not a calibrated normal-distribution z-score. The five-day horizon and clipping bounds were not inferred from the cited papers or optimised on these historical results.')
equation('Baseline reversal score',r's^{\mathrm{base}}_{i,t}=-x_{i,t}',
 'Equation 3 assigns a negative raw score to a positive recent movement. The sign expresses the reversal hypothesis discussed in Section 1; it is followed by portfolio construction rather than interpreted directly as an order.')
listing('Constructing the historical reversal score',baseline_decisions,'        volatility =','        betas.iloc[t]')

heading('3.1. Beta estimation and interpretation',sub=True)
p('In <i>Capital Asset Prices</i> (1964), Sharpe develops the relationship between asset risk and market equilibrium [3]. This supplies the context for measuring systematic market sensitivity. The implementation below uses a trailing OLS slope to SPY as an operational estimate; it does not assume that the CAPM describes every stock return.')
equation('Trailing market-beta estimate',r'\widehat{\beta}_{i,t}=\frac{\sum_{u=t-m+1}^{t}(r_{i,u}-\bar r_i)(r_{M,u}-\bar r_M)}{\sum_{u=t-m+1}^{t}(r_{M,u}-\bar r_M)^2}',
 'Equation 4 is the intercept-inclusive OLS slope. Where: m = 126, M identifies SPY and the bars denote means within that trailing window. A benchmark window with negligible variance is rejected. Each estimate is available at its decision close and is shifted before execution.')
p('Fama and French, in <i>Common risk factors in the returns on stocks and bonds</i> (1993), identify common equity variation beyond the overall market factor [4]. Therefore, neutralising a single SPY beta does not establish neutrality to every economic risk. This milestone does not constrain sector, size, value or momentum exposure.')

heading('4. Portfolio construction and exposure limits',True)
p('Golub and Van Loan discuss least-squares and rank-deficient problems in <i>Matrix Computations</i> (2013), particularly Chapter 5 [14]. Using that standard projection framework, this project removes the components of each score that load on the constant vector and the estimated market-beta vector. A least-squares solve is used in the code so that identical beta estimates do not require an invertible normal-equations matrix.')
equation('Projection away from dollar and estimated-beta exposure',r'A_t=[\mathbf{1},\widehat{\beta}_t],\qquad q_t=s_t-A_t A_t^{+}s_t',
 'Equation 5 defines the projected score q. Where: A contains the two exposure directions and A+ denotes the Moore-Penrose pseudoinverse. The final weights are obtained by uniform rescaling. An effectively zero projected score gives a flat portfolio.')
equation('Target portfolio constraints',r'\mathbf{1}^{T}w_t=0,\quad \widehat{\beta}_t^{T}w_t=0,\quad \|w_t\|_1\leq G,\quad \|w_t\|_{\infty}\leq b',
 'Equation 6 states the operational definition of neutrality and the exposure ceilings. Where: G = 1 and b = 0.08. At full utilisation, gross exposure is approximately 50% long plus 50% short. If the name limit binds, all positions shrink by the same factor; clipping names independently would generally disturb the exposure constraints.')
listing('Preserving neutrality while enforcing a position ceiling',neutral_weights,'    exposures =','    return weights')
p('The constraints apply to post-cost target weights at the rebalance. The beta vector is an estimate from the previous decision close. Subsequent price drift and estimation error can produce realised beta even when the recorded estimated exposure is numerically zero.')

heading('5. Graph relationships and diffusion',True)
p('As Mantegna explains in <i>Hierarchical structure in financial markets</i> (1999), a stock-return correlation matrix can support a graph representation that reveals an economically meaningful organisation [6]. His minimum-spanning-tree construction is not reproduced here. The project uses a symmetric union of positive-correlation neighbour selections, preserving up to five directed neighbours above 0.20 before symmetrisation.')
p('Chung introduces graph Laplacians and their spectra in <i>Spectral Graph Theory</i> (1997) [7]. The distinction between Laplacian conventions matters: Equation 7 uses the combinatorial D - W matrix divided by the mean weighted degree, rather than the symmetric degree-normalised Laplacian emphasised in much of Chung\'s treatment.')
equation('Scaled combinatorial graph Laplacian',r'D_{ii}=\sum_j W_{ij},\qquad L=\frac{D-W}{\bar d}',
 'Equation 7 defines W as the symmetric adjacency matrix and d-bar as the mean weighted degree. An empty graph uses L = 0. The scale choice is specific to this project and gives the diffusion-time parameter a more comparable magnitude as connectivity changes.')
p('Kondor and Lafferty, in <i>Diffusion Kernels on Graphs and Other Discrete Input Spaces</i> (2002), construct graph kernels through matrix exponentiation and connect them to heat diffusion [8]. This motivates the smoothing operator in Equation 8. It does not establish that its residual is a profitable financial signal.')
equation('Graph heat diffusion',r'\widetilde{x}_t=\exp(-\tau L_t)x_t',
 'Equation 8 smooths the observed shock over the graph. Where: tau = 1 in the current prototype. The implementation uses a symmetric eigendecomposition and has been checked against a direct matrix exponential, constant preservation and decreasing graph energy.')
equation('Proposed graph-relative reversal score',r's_t^{\mathrm{graph}}=-(x_t-\widetilde{x}_t)',
 'Equation 9 is the proposed trading rule. It reverses deviations from the diffused value before applying the same portfolio constraints. The graph score was first checked on synthetic data; its historical comparison is reported in Section 8.')

heading('5.1. Interactive view of the historical structure',True)
figure('Historical 126-session correlation matrix at the last validation date',ROOT/'outputs/historical/05-correlation-snapshot.png',height=350)
p('Figure 1 gives a static view of the last validation snapshot. The companion <b>Historical-Correlation-Explorer.html</b> contains 120 monthly frames, with rotation, zoom, a date slider and playback. Each frame uses trailing observations through the displayed date; no final-holdout data enter the surface.')
p('The surface height is correlation, not expected return. Asset order remains fixed and the asset axes are discrete. The mesh joins neighbouring cells only for display, so values between stock labels should not be interpreted as estimated relationships between intermediate assets. The full correlation matrix is also distinct from the thresholded neighbour graph used by the strategy.')

heading('6. Execution timing and portfolio accounting',True)
p('The accounting convention is deliberately explicit: a close-t observation produces a decision, the decision trades at close t+1, and the newly formed position first earns the return ending at close t+2. This is a modelling convention chosen to avoid obtaining a close price and simultaneously earning the return ending at that same close. It remains an approximation to executable orders.')
listing('Delaying decisions before slicing the evaluation phase',phase_inputs,'    execution =','    if mask.sum()')
p('Listing 3 shows why the shift occurs before period slicing. The first execution in a phase may use the preceding session\'s valid decision, but each phase begins with a flat book and fresh capital. The final close liquidates positions. Thus neither entry costs nor terminal closing costs disappear at an evaluation boundary.')
equation('Short-borrow accrual',r'B_t=a\frac{\Delta_t}{365}\sum_i\max(-v_{i,t-1},0)',
 'Equation 10 charges the annual rate a on the prior close\'s absolute short notional v. Delta counts elapsed calendar days, including weekends. This uniform borrow assumption is illustrative; it is not a historical security-level borrow series.')
equation('Post-cost NAV and drift-aware trading cost',r'V_t^{\mathrm{after}}+c\sum_i|w_{i,t}V_t^{\mathrm{after}}-v_{i,t}^{\mathrm{marked}}|=V_t^{\mathrm{before}}',
 'Equation 11 solves for NAV after trading fees. Where: c is the per-dollar fee and marked notionals incorporate the day\'s price changes. NAV before trading already reflects P&amp;L and borrow. The scalar solve makes target weights refer to equity after fees, avoiding a small exposure overshoot caused solely by transaction costs.')
equation('Net-return reconciliation',r'R_t^{\mathrm{net}}=\frac{\mathrm{PnL}_t-C_t-B_t}{V_{t-1}^{\mathrm{after}}}',
 'Equation 12 reconciles gross position P&amp;L, trading cost C and borrow cost B to net return. Turnover counts every dollar bought and every dollar sold, divided by start-of-day NAV. Cash interest, financing rebates, margin constraints and nonlinear market impact are not included.')
listing('Solving for equity after transaction costs',execute_targets,'        def balance(after):','        new_notionals =')

story.append(Spacer(1,18))
heading('7. Historical baseline results')
rows=[['Metric','Development','Validation']]
for field,label,fmt in [('total_return','Total net return','.2%'),('annualised_return','Annualised net return','.2%'),('annualised_volatility','Annualised volatility','.2%'),('sharpe_zero_cash_rate','Zero-cash-rate Sharpe','.2f'),('maximum_drawdown','Maximum drawdown','.2%'),('realized_market_beta','Realised SPY beta','.4f'),('mean_turnover','Mean daily turnover','.2%'),('mean_gross_exposure','Mean gross exposure','.2%'),('max_abs_net_exposure','Maximum absolute dollar exposure','.2e'),('max_abs_estimated_beta','Maximum absolute estimated beta','.2e')]:
    rows.append([label,format(d[field],fmt),format(v[field],fmt)])
table('Baseline performance at 5 bps and 2% annual short borrow',rows,[.5,.25,.25])
p(f'Table {counts["Table"]} reports a negative annualised return in both phases: {d.annualised_return:.2%} in development and {v.annualised_return:.2%} in validation. The numerical exposure constraints are satisfied, but these constraints do not imply a viable strategy. The practical issue is whether the signal can earn enough before costs to support its turnover.')
p('Lo, in <i>The Statistics of Sharpe Ratios</i> (2002), explains why return dependence and estimation error affect Sharpe-ratio interpretation [11]. The statistic below uses the conventional square-root-of-time scaling and a zero cash rate for descriptive comparison. It is not a dependence-adjusted significance test or a confidence interval.')
equation('Descriptive annualised Sharpe statistic',r'\widehat{S}=\sqrt{252}\,\frac{\overline{R^{\mathrm{net}}}}{s(R^{\mathrm{net}})}',
 'Equation 13 uses the sample daily standard deviation. It is labelled as a zero-cash-rate statistic because cash interest is not modelled. Comparisons with an external fund\'s published Sharpe would require matching return and financing conventions.')
equation('Drawdown from the running capital peak',r'DD_t=\frac{V_t}{\max(V_0,V_1,\ldots,V_t)}-1',
 'Equation 14 includes initial capital in the running peak, so an early loss is counted. The reported maximum drawdown is the most negative observed value, including the final liquidation date.')

heading('7.1. Capital paths and cost sensitivity',sub=True)
figure('Net historical capital and drawdown; phases start with separate capital',ROOT/'outputs/historical/03-historical-baseline.png')
rows=[['Cost per dollar','Development CAGR','Validation CAGR']]
for fee in protocol['cost_scenarios_bps']:
    part=summary[summary.trading_cost_bps==fee].set_index('phase')
    rows.append([f'{fee:g} bps',f'{part.loc["development","annualised_return"]:.2%}',f'{part.loc["validation","annualised_return"]:.2%}'])
table('All predeclared trading-cost scenarios; short borrow remains 2%',rows,[.34,.33,.33])
p('The zero-trading-fee scenario is not a costless portfolio: it still pays short borrow. Development is positive under that scenario, whereas validation is negative. Consequently, the validation failure cannot be attributed only to the 5 bps trading-fee assumption. The signal itself requires a stronger empirical comparison.')

heading('7.2. Interpretation and remaining uncertainty')
figure('Sensitivity to trading costs and rolling realised market beta',ROOT/'outputs/historical/04-costs-and-beta.png')
p('Figure 3 demonstrates two separate issues. Net returns decline as the stated cost per dollar increases. Realised beta also varies through time despite the target constraint. The variation reflects an estimated hedge, a finite rolling measurement window and changing returns; it is not a contradiction of the recorded numerical neutrality checks.')
p('Bailey and colleagues, in <i>The probability of backtest overfitting</i> (2017), emphasise that a held-out sample alone does not account for repeated strategy searches [10]. For this reason, the project records each experiment and does not interpret its chronological split as proof against overfitting. No PBO estimate, CSCV analysis or White reality-check statistic has been calculated in this milestone.')
p('The comparison in Section 8 retains these dates, costs, exposure ceilings and execution rules, including the unfavourable results. Any subsequent tuning must be confined to the development process and documented before the reserved final test is released.')

add_graph_comparison(ROOT,p,heading,table,equation,figure,listing,counts)

heading('9. Planned persistent-homology extension',True)
p('Edelsbrunner, Letscher and Zomorodian formalise feature persistence through a filtration in <i>Topological Persistence and Simplification</i> (2002) [12]. Their framework motivates measuring how connected components and loops appear and disappear as a scale changes. Persistence is a mathematical description of structure, not by itself a financial prediction.')
equation('Correlation-derived distance for the proposed topology study',r'd_{ij,t}=\sqrt{2(1-\rho_{ij,t})}',
 'Equation 21 relates correlation to a distance between standardised return series, following the financial correlation-distance construction associated with Mantegna [6]. It will use a complete valid correlation matrix; the sparse positive-neighbour adjacency matrix must not be substituted for that metric space.')
p('Gidea and Katz, in <i>Topological data analysis of financial time series: Landscapes of crashes</i> (2018), study persistence landscapes from sliding-window point clouds of market-index returns [13]. That is relevant precedent, but the planned asset correlation-distance construction here is different. Their findings do not establish that our proposed H0/H1 features will improve trading performance.')
p('The extension will require numerical checks on known shapes, explicit treatment of infinite H0 bars, stable feature definitions and training-only thresholds. Mean correlation and realised volatility will serve as simpler controls. The persistent-homology module remains unimplemented in this milestone.')

heading('10. Reproducibility and subsequent milestones',True)
table('Research artifacts and completion state',[
 ['Artifact','Current status'],['Historical data and protocol','Cached inputs, source metadata, SHA-256 hashes and guarded period boundaries'],['Baseline backtest','Reproduced from Milestone 2 within saved rounding tolerance'],['Graph trading comparison','44 predeclared backtests completed; paired intervals and exposure controls reported'],['Interactive 3D explorers','120 monthly correlation surfaces and 120 graph/score frames'],['Persistent homology','Planned; no extracted features or regime results claimed'],['Final holdout','2020-2025 reserved; not acquired or evaluated'],['GitHub readiness','Requirements, 25 checks, three notebooks, rebuild scripts and CI configuration'],['Public repository / LinkedIn page','Planned for final presentation; not published by this milestone']],[.33,.67])
p('The private research bundle retains the acquired observations for exact offline replay. A public GitHub checkout will exclude provider input caches and regenerate them through the acquisition script. Provider revisions can change a fresh download, so the recorded hashes distinguish exact snapshot reproduction from rerunning the same method on a new data vintage. Permission to redistribute vendor data is not inferred from its technical accessibility.')
p('The paper builder extracts its code excerpts directly from the research modules and generates the contents and lists from captions. Future versions will retain the title page, abstract, abbreviations, symbol definitions, numbered equations, figure and table lists, code listings and author-led references. The final public presentation will explain both the results and the limits of the evidence.')

heading('References',True)
for ref in refs:
    p(f'[{ref["id"]}] {escape(ref["authors"])} ({ref["year"]}). <i>{escape(ref["title"])}</i>. {escape(ref["venue"])}. <link href="{escape(ref["url"])}" color="#176960">'+('DOI: '+escape(ref['doi']) if 'doi' in ref else 'Primary data record')+'</link>.','SmallText')
p('References 1-14 and 16-18 are journal articles, scholarly books or a peer-reviewed conference paper. Reference 15 identifies the primary data service. The source register records the accessed version and the role of each reference. No citation is intended to imply that another author tested this project\'s exact strategy.','SmallText')

doc=Paper(str(OUT/'Market-Neutral-Trading-Algorithm-Milestone-3-Paper.pdf'),pagesize=A4,leftMargin=54,rightMargin=54,topMargin=62,bottomMargin=52,title='Market-Neutral Trading Algorithm - Milestone 3',author='Joel Cerraga')
doc.addPageTemplates(PageTemplate(id='paper',frames=Frame(54,52,WIDTH,A4[1]-114,id='normal'),onPage=page))
doc.multiBuild(story)
(ROOT/'paper/manuscript.md').write_text('\n\n'.join(md),encoding='utf-8')
bib=[]
for r in refs:
    fields={'author':r.get('bibtex_author',r['authors']),'title':r['title'],'year':r['year'],'url':r['url']}
    fields.update(r.get('bibtex_fields',{'note':r['venue']}))
    if 'doi' in r:fields['doi']=r['doi']
    bib.append('@'+r['type']+'{'+r['key']+',\n'+',\n'.join('  '+k+' = {'+str(v)+'}' for k,v in fields.items())+'\n}')
(ROOT/'paper/references.bib').write_text('\n\n'.join(bib),encoding='utf-8')
manifest={'counts':counts,'references':len(refs),'scientific_references':17,'code_sources':{str(Path(inspect.getsourcefile(f)).relative_to(ROOT)):hashlib.sha256(Path(inspect.getsourcefile(f)).read_bytes()).hexdigest() for f in [baseline_decisions,neutral_weights,phase_inputs,execute_targets,match_gross_exposure,stationary_indices,hac_mean_interval,build_decisions]}}
(OUT/'milestone-3-paper-manifest.json').write_text(json.dumps(manifest,indent=2))
print(json.dumps(manifest,indent=2))
