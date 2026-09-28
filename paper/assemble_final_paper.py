"""Assemble the final A4 portrait paper from the verified Markdown manuscript.

Requires XeLaTeX with fontspec, unicode-math, booktabs, longtable, fvextra,
caption, tocloft and the Nimbus Sans / DejaVu Sans Mono fonts. No backtest is
rerun and no research input or result is changed by this presentation build.
"""
from pathlib import Path
import argparse
import hashlib
import json
import re
import shutil
import subprocess

ROOT=Path(__file__).resolve().parents[1]
PAPER=ROOT/'paper'
OUT=PAPER/'final'
NAME='Market-Neutral-Trading-Algorithm-Final-Paper'

PREAMBLE=r'''\documentclass[12pt,a4paper,oneside]{article}
\usepackage[a4paper,left=23mm,right=23mm,top=21mm,bottom=21mm,headheight=12pt,headsep=7mm,footskip=11mm]{geometry}
\usepackage{fontspec}
\setmainfont{NimbusSans}[Path=/usr/share/fonts/opentype/urw-base35/,UprightFont=*-Regular.otf,BoldFont=*-Bold.otf,ItalicFont=*-Italic.otf,BoldItalicFont=*-BoldItalic.otf]
\setsansfont{NimbusSans}[Path=/usr/share/fonts/opentype/urw-base35/,UprightFont=*-Regular.otf,BoldFont=*-Bold.otf,ItalicFont=*-Italic.otf,BoldItalicFont=*-BoldItalic.otf]
\setmonofont{DejaVu Sans Mono}[Scale=0.81]
\usepackage{unicode-math}
\setmathfont{Latin Modern Math}
\usepackage{amsmath}
\usepackage{graphicx,booktabs,array,longtable,ragged2e}
\usepackage[table]{xcolor}
\definecolor{tablehead}{RGB}{234,238,241}
\definecolor{tablerule}{RGB}{205,211,215}
\definecolor{codebg}{RGB}{247,248,249}
\usepackage{caption}
\DeclareCaptionFont{papercap}{\fontsize{10}{12}\selectfont}
\captionsetup{font={papercap,it},labelfont=it,labelsep=period,justification=centering,singlelinecheck=false,skip=6pt}
\captionsetup[table]{position=bottom}
\usepackage{fvextra}
\usepackage{needspace,placeins,titlesec,tocloft,fancyhdr,enumitem}
\usepackage{xurl}
\usepackage[hidelinks,unicode,pdfusetitle,bookmarksnumbered=true]{hyperref}
\hypersetup{pdftitle={Market-Neutral Trading Algorithm},pdfauthor={Joel Cerraga},pdfsubject={Graph diffusion, persistent homology and reproducible empirical research}}
\urlstyle{same}
\usepackage{setspace}
\setstretch{1.11}
\setlength{\parindent}{0pt}
\setlength{\parskip}{6pt plus 1pt minus 1pt}
\setlength{\emergencystretch}{2em}
\tolerance=1800
\pretolerance=800
\hyphenpenalty=250
\widowpenalty=10000
\clubpenalty=10000
\raggedbottom
\setcounter{secnumdepth}{2}
\setcounter{tocdepth}{2}
\titleformat{\section}{\normalfont\fontsize{15}{18}\bfseries}{\thesection}{0.7em}{}
\titleformat{\subsection}{\normalfont\fontsize{12}{15}\bfseries}{\thesubsection}{0.7em}{}
\titlespacing*{\section}{0pt}{15pt plus 2pt minus 1pt}{7pt}
\titlespacing*{\subsection}{0pt}{11pt plus 2pt minus 1pt}{4pt}
\pagestyle{fancy}
\fancyhf{}
\fancyhead[R]{\fontsize{8}{10}\selectfont MARKET-NEUTRAL TRADING ALGORITHM\enspace |\enspace JOEL CERRAGA}
\fancyfoot[C]{\fontsize{10}{12}\selectfont\thepage}
\renewcommand{\headrulewidth}{0pt}
\renewcommand{\footrulewidth}{0pt}
\fancypagestyle{plain}{\fancyhf{}\fancyfoot[C]{\fontsize{10}{12}\selectfont\thepage}\renewcommand{\headrulewidth}{0pt}}
\setlength{\intextsep}{9pt plus 2pt minus 1pt}
\setlength{\textfloatsep}{10pt plus 2pt minus 1pt}
\setlength{\floatsep}{10pt plus 2pt minus 1pt}
\renewcommand{\topfraction}{.95}
\renewcommand{\bottomfraction}{.85}
\renewcommand{\textfraction}{.07}
\renewcommand{\floatpagefraction}{.85}
\setcounter{topnumber}{4}\setcounter{bottomnumber}{3}\setcounter{totalnumber}{6}
\setlength{\LTpre}{5pt}\setlength{\LTpost}{6pt}
\setlength{\LTleft}{0pt}\setlength{\LTright}{0pt}
\setlength{\LTcapwidth}{\textwidth}
\setlength{\tabcolsep}{5pt}
\newcolumntype{P}[1]{>{\RaggedRight\arraybackslash}p{#1}}
\newcolumntype{Q}[1]{>{\RaggedLeft\arraybackslash}p{#1}}
\newlistof{equations}{loe}{List of equations}
\newlistof{codelistings}{lol}{List of code listings}
\renewcommand{\cftfigpresnum}{Figure\space}\setlength{\cftfignumwidth}{4.6em}
\renewcommand{\cfttabpresnum}{Table\space}\setlength{\cfttabnumwidth}{4.6em}
\renewcommand{\cftequationspresnum}{Equation\space}\setlength{\cftequationsnumwidth}{5.8em}
\renewcommand{\cftcodelistingspresnum}{Listing\space}\setlength{\cftcodelistingsnumwidth}{4.8em}
\setlength{\cftbeforesecskip}{3pt}
\setlength{\cftbeforesubsecskip}{1pt}
\setlength{\cftbeforefigskip}{3pt}\setlength{\cftbeforetabskip}{3pt}
\setlength{\cftbeforeequationsskip}{3pt}\setlength{\cftbeforecodelistingsskip}{3pt}
\renewcommand{\cfttoctitlefont}{\fontsize{16}{20}\bfseries}
\renewcommand{\cftloftitlefont}{\fontsize{15}{18}\bfseries}
\renewcommand{\cftlottitlefont}{\fontsize{15}{18}\bfseries}
\renewcommand{\cftloetitlefont}{\fontsize{15}{18}\bfseries}
\renewcommand{\cftloltitlefont}{\fontsize{15}{18}\bfseries}
\setlength{\cftbeforetoctitleskip}{0pt}\setlength{\cftaftertoctitleskip}{10pt}
\setlength{\cftbeforeloftitleskip}{8pt}\setlength{\cftafterloftitleskip}{8pt}
\setlength{\cftbeforelottitleskip}{8pt}\setlength{\cftafterlottitleskip}{8pt}
\setlength{\cftbeforeloetitleskip}{8pt}\setlength{\cftafterloetitleskip}{8pt}
\setlength{\cftbeforeloltitleskip}{8pt}\setlength{\cftafterloltitleskip}{8pt}
\newcommand{\paperequation}[3]{%
  \par\addvspace{3pt}\noindent\begin{minipage}{\linewidth}
  \begin{equation}\label{eq:#1}#3\tag{#1}\end{equation}
  \vspace{-8pt}\begin{center}\fontsize{10}{12}\selectfont\itshape Equation #1. #2\end{center}
  \addcontentsline{loe}{equations}{\protect\numberline{#1}#2}
  \end{minipage}\par\addvspace{4pt}}
\newcommand{\listingcaption}[2]{%
  \phantomsection\label{lst:#1}%
  \begin{center}\fontsize{10}{12}\selectfont\itshape Listing #1. #2\end{center}
  \addcontentsline{lol}{codelistings}{\protect\numberline{#1}#2}}
\newcommand{\bodyheading}[1]{\clearpage\section{#1}}
\newcommand{\frontheading}[1]{\clearpage\phantomsection\section*{#1}\addcontentsline{toc}{section}{#1}}
\newcommand{\sourcemeta}[1]{\par{\fontsize{9.2}{12}\selectfont #1\par}\vspace{2pt}}
\newcommand{\refentry}[1]{\par\begingroup\hangindent=7mm\hangafter=1 #1\par\endgroup\vspace{4pt}}
\begin{document}
\begin{titlepage}
\thispagestyle{empty}
\centering
\vspace*{28mm}
{\fontsize{24}{29}\selectfont\bfseries Market-Neutral Trading Algorithm\par}
\vspace{10mm}
{\fontsize{14}{19}\selectfont Graph diffusion, persistent homology and\\reproducible empirical research\par}
\vspace{24mm}
{\fontsize{12}{17}\selectfont Joel Cerraga\par}
\vspace{6mm}
{\fontsize{12}{17}\selectfont Quantitative research project\par}
\vspace{6mm}
{\fontsize{12}{17}\selectfont March 2026\par}
\vspace{6mm}
{\fontsize{11}{15}\selectfont Final assembled paper\par}
\vfill
\end{titlepage}
\pagenumbering{roman}
\thispagestyle{plain}
'''

MATH_UNICODE={
 'σ̂':r'\(\widehat{\sigma}\)','β̂':r'\(\widehat{\beta}\)','x̃':r'\(\widetilde{x}\)',
 'd̄':r'\(\bar d\)','c̄':r'\(\bar c\)','θ̂':r'\(\widehat{\theta}\)',
 '𝒟':r'\(\mathcal D\)','𝒪':r'\(\mathcal O\)','⁺':r'\(^{+}\)',
 '⁻⁶':r'\(^{-6}\)','⁶':r'\(^{6}\)','₂':r'\(_2\)','²':r'\(^{2}\)',
 '√252':r'\(\sqrt{252}\)','√':r'\(\sqrt{\phantom{x}}\)',
 '−':r'\( - \)','×':r'\(\times\)','ℓ':r'\(\ell\)',
 'α':r'\(\alpha\)','β':r'\(\beta\)','γ':r'\(\gamma\)','δ':r'\(\delta\)',
 'ε':r'\(\varepsilon\)','η':r'\(\eta\)','θ':r'\(\theta\)','λ':r'\(\lambda\)',
 'μ':r'\(\mu\)','ξ':r'\(\xi\)','ρ':r'\(\rho\)','σ':r'\(\sigma\)',
 'τ':r'\(\tau\)','Δ':r'\(\Delta\)','Ω':r'\(\Omega\)',
}
CHAR_ESC={'&':r'\&','%':r'\%','$':r'\$','#':r'\#','_':r'\_','{':r'\{','}':r'\}',
          '\\':r'\textbackslash{}','~':r'\textasciitilde{}','^':r'\textasciicircum{}'}


def escape_text(text):
    # Unicode combining accents are handled before single-character substitutions.
    keys=sorted(MATH_UNICODE,key=len,reverse=True)
    parts=re.split('('+'|'.join(map(re.escape,keys))+')',text)
    return ''.join(MATH_UNICODE[p] if p in MATH_UNICODE else ''.join(CHAR_ESC.get(c,c) for c in p) for p in parts)


def inline(text):
    # DOI URLs may contain balanced parentheses, e.g. 0304-405X(93)90023-5.
    link_pattern=r'\[[^\]]+\]\((?:[^()]|\([^()]*\))+\)'
    pattern=r'(`[^`]+`|'+link_pattern+r'|\*\*[^*]+\*\*|(?<!\*)\*[^*]+\*(?!\*))'
    parts=re.split(pattern,text)
    out=[]
    for part in parts:
        if part.startswith('`') and part.endswith('`'):
            code = part[1:-1]
            if ' ' in code:
                # URL typesetting discards spaces; command arguments must remain separate.
                out.append(r'{\ttfamily\fontsize{11.5}{13}\selectfont '+escape_text(code)+'}')
            else:
                out.append(r'{\fontsize{9.3}{12}\selectfont\nolinkurl{'+code+'}}')
        elif re.fullmatch(link_pattern,part):
            m=re.fullmatch(r'\[([^\]]+)\]\(((?:[^()]|\([^()]*\))+)\)',part);label,url=m.groups()
            original_url=url
            url=url.replace('%',r'\%').replace('#',r'\#')
            if label==original_url:out.append(r'\url{'+url+'}')
            else:out.append(r'\href{'+url+'}{'+escape_text(label)+'}')
        elif part.startswith('**'):
            out.append(r'\textbf{'+escape_text(part[2:-2])+'}')
        elif part.startswith('*'):
            out.append(r'\textit{'+escape_text(part[1:-1])+'}')
        else:
            # Link explanatory references to the numbered objects.
            subparts=re.split(r'((?:Equation|Figure|Table|Listing) \d+)',part)
            for bit in subparts:
                m=re.fullmatch(r'(Equation|Figure|Table|Listing) (\d+)',bit)
                if m:
                    prefix={'Equation':'eq','Figure':'fig','Table':'tab','Listing':'lst'}[m[1]]
                    out.append(r'\hyperref['+prefix+':'+m[2]+']{'+escape_text(bit)+'}')
                else:out.append(escape_text(bit))
    return ''.join(out)


EQ_OVERRIDES={
 21:r'''\begin{aligned}
 u_{i,t}&=\frac{r_{i,t-W_{\mathrm{len}}+1:t}-\bar r_{i,t}\mathbf{1}}{\left\|r_{i,t-W_{\mathrm{len}}+1:t}-\bar r_{i,t}\mathbf{1}\right\|_2},\\[4pt]
 d_{ij,t}&=\sqrt{2(1-\rho_{ij,t})}=\|u_{i,t}-u_{j,t}\|_2
 \end{aligned}''',
 23:r'''\begin{aligned}
 \ell_a&=d_a-b_a,\\[3pt]
 f_{0,\mathrm{mean}}&=\frac{1}{n-1}\sum_{a\in\mathcal D_0^{\mathrm{fin}}}\ell_a,
 &f_{0,\max}&=\max_{a\in\mathcal D_0^{\mathrm{fin}}}\ell_a,\\[3pt]
 f_{1,\mathrm{total}}&=\sum_{a\in\mathcal D_1}\ell_a,
 &f_{1,\max}&=\max_{a\in\mathcal D_1}\ell_a
 \end{aligned}''',
 24:r'''\begin{aligned}
 z_{j,t}&=\frac{c_{j,t}-\bar c_{j,\mathrm{dev}}}{s_{j,\mathrm{dev}}},\\[3pt]
 \widehat\theta&=\arg\min_{\theta}\sum_{t\in\mathrm{dev}}\big(f_t-[1,z_t^\top]\theta\big)^2,\\[3pt]
 \widehat f_t&=[1,z_t^\top]\widehat\theta
 \end{aligned}''',
 27:r'''\begin{aligned}
 g_a(\varepsilon)&=\max\{0,\min(\varepsilon-b_a,d_a-\varepsilon)\},\\[3pt]
 \lambda_k(\varepsilon)&=\operatorname{kth\ largest}_{a}\,g_a(\varepsilon)
 \end{aligned}''',
 29:r'''\xi_t=\begin{pmatrix}R^{B,\mathrm{net}}_t\\R^{G,\mathrm{net}}_t\\R^{G,\mathrm{net}}_t-R^{B,\mathrm{net}}_t\end{pmatrix},
 \qquad \widehat\mu_j=252\,\overline{\xi}_j,\quad j=1,2,3''',
 30:r'''\begin{gathered}
 \Pr\!\left(\bigcup_{j=1}^{m_F}\{\mu_j\notin I_j\}\right)
 \leq\sum_{j=1}^{m_F}\Pr(\mu_j\notin I_j)\leq\alpha,\\[4pt]
 m_F=3,\qquad\alpha=0.05,\\[4pt]
 \Pr(\mu_j\in I_j)\geq1-\frac{\alpha}{m_F}=0.98333\ldots
 \end{gathered}'''
}

# Fractions sum to one. Widths exclude the padding from each table column.
TABLE_WIDTHS={1:[.23,.77],2:[.29,.71],3:[.30,.70],4:[.20,.24,.56],5:[.33,.67],6:[.35,.65],
 7:[.49,.255,.255],8:[.24,.38,.38],9:[.28,.72],10:[.28,.145,.145,.15,.14,.14],
 11:[.22,.185,.185,.20,.21],12:[.19,.21,.30,.30],13:[.22,.195,.195,.195,.195],14:[.30,.70],
 15:[.44,.28,.28],16:[.44,.28,.28],17:[.22,.195,.195,.195,.195],18:[.32,.68],19:[.46,.27,.27],
 20:[.32,.14,.27,.27],21:[.46,.27,.27],22:[.28,.18,.18,.18,.18],23:[.28,.36,.36],24:[.24,.38,.38],
 25:[.18,.23,.21,.19,.19],26:[.17,.35,.48],27:[.29,.71]}
TEXT_TABLES={1,2,3,4,5,6,9,14,18,26,27}


SYMBOL_ROWS=[
 r'i,j;\ t;\ n',r'P;\ r',r'h;\ \widehat\sigma',r'x;\ s',r'\beta;\ \widehat\beta',
 r'A;\ A^{+}',r'q;\ w',r'G;\ b',r'\rho;\ W;\ D',r'\bar d;\ L;\ \tau',
 r'\widetilde x;\ d(i,j)',r'v;\ V;\ c',r'a;\ \Delta',r'B;\ C',r'R;\ S;\ DD',
 r'G^{*};\ {}^{B};\ {}^{G}',r'\delta;\ \mu;\ T',r'\ell;\ I^{*}',r'K;\ \gamma;\ \Omega',
 r'\mathrm{SE};\ \lambda',r'W_{\mathrm{len}};\ \varepsilon',r'\mathcal D_q;\ b_a;\ d_a;\ \ell_a',
 r'\lambda_k(\varepsilon)',r'd_B;\ \eta',r'z;\ \widehat\theta;\ R^2',r'\mathbb F_2',
 r'\alpha;\ m_F;\ I_j',r'\xi_t;\ \mu_j',r'\mathcal O'
]


def table_tex(number,title,lines):
    rows=[[c.strip() for c in line.strip().strip('|').split('|')] for line in lines]
    rows=[rows[0]]+rows[2:]
    n=len(rows[0]);fractions=TABLE_WIDTHS.get(number,[1/n]*n)
    assert abs(sum(fractions)-1)<1e-8,(number,fractions)
    assert all(len(row)==n for row in rows),(number,rows)
    spec=''.join(('P' if number in TEXT_TABLES or i==0 else 'Q')+'{'+f'{f:.6f}'+r'\dimexpr\textwidth-'+str(2*n)+r'\tabcolsep\relax}' for i,f in enumerate(fractions))
    header=r'\rowcolor{tablehead} '+ ' & '.join(r'\textbf{'+inline(c)+'}' for c in rows[0])+r' \\ \midrule'
    is_long = number in {1,2}
    body=[r'\begingroup',r'\setcounter{table}{'+str(number-1)+'}',r'\setstretch{1}\fontsize{10}{12.5}\selectfont',r'\renewcommand{\arraystretch}{1.12}',r'\arrayrulecolor{tablerule}']
    # Keep the one-page setback chapter together without reducing its type size.
    if number == 26:
        body += [r'\renewcommand{\arraystretch}{1.06}',
                 r'\setlength{\aboverulesep}{1pt}\setlength{\belowrulesep}{1pt}']
    if is_long:
        body += [r'\setlength{\aboverulesep}{1pt}\setlength{\belowrulesep}{1pt}']
        body += [r'\begin{longtable}{'+spec+'}',r'\toprule',header,r'\endfirsthead',r'\toprule',header,r'\endhead',r'\endfoot',r'\endlastfoot']
    else:
        body += [r'\begin{table}[!htbp]',r'\centering',r'\setstretch{1}\fontsize{10}{12.5}\selectfont',r'\begin{tabular}{'+spec+'}',r'\toprule',header]
    for i,row in enumerate(rows[1:]):
        cells = [inline(c) for c in row]
        if number == 2:
            cells[0] = r'\('+SYMBOL_ROWS[i]+r'\)'
        end=r' \\*' if is_long and i>=len(rows)-3 else r' \\'
        body.append(' & '.join(cells)+end)
        if i<len(rows)-2:body.append(r'\midrule[0.2pt]')
    body.append(r'\bottomrule')
    if is_long:
        body += [r'\multicolumn{'+str(n)+r'}{@{}p{\textwidth}@{}}{\label{tab:'+str(number)+r'}\addcontentsline{lot}{table}{\protect\numberline{'+str(number)+r'}'+inline(title)+r'}\vspace{5pt}{\centering\fontsize{10}{12}\selectfont\itshape Table '+str(number)+'. '+inline(title)+r'\par}\vspace{3pt}}\\',r'\end{longtable}']
    else:
        body += [r'\end{tabular}',r'\caption{'+inline(title)+r'}\label{tab:'+str(number)+r'}',r'\end{table}']
    body.append(r'\endgroup')
    return '\n'.join(body)


def parse_blocks(text,front=False):
    lines=text.splitlines();out=[];i=0;pending_listing=None
    while i<len(lines):
        line=lines[i].strip()
        if not line:i+=1;continue
        h=re.match(r'^#{2,3} (.+)',line)
        if h:
            title=h[1]
            if front:out.append(r'\frontheading{'+inline(title)+'}')
            elif title.startswith('Appendix A.'):
                out.append(r'\clearpage\appendix\titleformat{\section}{\normalfont\fontsize{15}{18}\bfseries}{Appendix \thesection}{0.7em}{}')
                out.append(r'\section{'+inline(title.split('. ',1)[1])+'}')
            elif re.match(r'^\d+\. ',title):out.append(r'\bodyheading{'+inline(re.sub(r'^\d+\. ','',title))+'}')
            elif re.match(r'^(?:\d+\.\d+\.|A\.\d+\.) ',title):out.append(r'\Needspace{4\baselineskip}\subsection{'+inline(re.sub(r'^(?:\d+\.\d+\.|A\.\d+\.) ','',title))+'}')
            else:raise ValueError('Unknown heading '+title)
            i+=1;continue
        m=re.match(r'^Table (\d+)\. (.+)',line)
        if m:
            number=int(m[1]);title=m[2];i+=1
            while i<len(lines) and not lines[i].strip():i+=1
            values=[]
            while i<len(lines) and lines[i].strip().startswith('|'):values.append(lines[i]);i+=1
            out.append(table_tex(number,title,values));continue
        m=re.match(r'^Equation (\d+)\. (.+)',line)
        if m:
            number=int(m[1]);title=m[2];i+=1
            while i<len(lines) and not lines[i].strip():i+=1
            tex=lines[i].strip();assert tex.startswith('$$') and tex.endswith('$$'),tex
            tex=tex[2:-2];tex=re.sub(r'\s*\\qquad\s*\('+str(number)+r'\)\s*$','',tex)
            tex=EQ_OVERRIDES.get(number,tex)
            out.append(r'\paperequation{'+str(number)+'}{'+inline(title)+'}{'+tex+'}');i+=1;continue
        m=re.match(r'^Listing (\d+)\. (.+)',line)
        if m:pending_listing=(int(m[1]),m[2]);i+=1;continue
        if line.startswith('```'):
            code=[];i+=1
            while i<len(lines) and not lines[i].startswith('```'):code.append(lines[i]);i+=1
            i+=1
            if pending_listing:
                number,title=pending_listing;pending_listing=None
                out.append(r'\par\addvspace{4pt}\noindent\begin{minipage}{\linewidth}')
                out.append(r'\begin{Verbatim}[fontsize=\small,baselinestretch=1.0,breaklines=true,breakanywhere=true,breakautoindent=true,breakindent=10pt,frame=single,framerule=.3pt,rulecolor=\color{tablerule},framesep=6pt,numbersep=5pt,numbers=left,xleftmargin=15pt,formatcom=\color{black}]')
                out[-1] += '\n' + '\n'.join(code) + '\n' + r'\end{Verbatim}'
                out.append(r'\listingcaption{'+str(number)+'}{'+inline(title)+'}')
                out.append(r'\end{minipage}\par\addvspace{4pt}')
            else:
                out.append(r'\begin{Verbatim}[fontsize=\small,breaklines=true]');out[-1] += '\n' + '\n'.join(code) + '\n' + r'\end{Verbatim}'
            continue
        m=re.match(r'^!\[Figure (\d+)\. ([^\]]+)\]\(([^)]+)\)',line)
        if m:
            number=int(m[1]);title=m[2];path=(PAPER/m[3]).resolve()
            dest=OUT/'assets'/f'figure-{number:02}.png';dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(path,dest)
            # Limit tall visuals to a portrait text-page fraction without distortion.
            # These chapter-ending figures leave room for the final paragraph,
            # preventing a two-line continuation before the next chapter break.
            width = r'.86\linewidth' if number in {12, 16} else r'\linewidth'
            out.extend([r'\begin{figure}[!htbp]',r'\centering',
                r'\includegraphics[width='+width+r',height=.65\textheight,keepaspectratio]{assets/'+dest.name+'}',
                r'\caption{'+inline(title)+'}'+r'\label{fig:'+str(number)+'}',r'\end{figure}'])
            i+=1;continue
        if line.startswith('- '):
            out.append(r'\begin{itemize}[nosep,leftmargin=1.5em]')
            while i<len(lines) and lines[i].strip().startswith('- '):out.append(r'\item '+inline(lines[i].strip()[2:]));i+=1
            out.append(r'\end{itemize}');continue
        paragraph=[line];i+=1
        while i<len(lines) and lines[i].strip() and not re.match(r'^(#|\||```|!\[|Equation \d|Table \d|Listing \d)',lines[i]):paragraph.append(lines[i].strip());i+=1
        content=inline(' '.join(paragraph))
        if paragraph[0].startswith('Source:'):out.append(r'\sourcemeta{'+content+'}')
        else:out.append(content+'\n')
    assert pending_listing is None
    return '\n\n'.join(out)


def assemble(compile_pdf=True):
    OUT.mkdir(parents=True,exist_ok=True)
    md=(PAPER/'manuscript.md').read_text()
    abstract=md.split('## Abstract\n\n',1)[1].split('## Table of contents',1)[0].strip()
    registers=md[md.index('## List of abbreviations'):md.index('## 1. Introduction')]
    body=md[md.index('## 1. Introduction'):md.index('## References\n\n')]
    reference_text,appendix_tail=md.split('## References\n\n',1)[1].split('## Appendix A. ',1)
    references=reference_text.strip().split('\n\n')
    appendix='## Appendix A. '+appendix_tail
    assert len(references)==24 and not any(x in '\n'.join(references) for x in ['Primary source','Not a scientific paper','Evidence:'])
    abstract_tex='\n\n'.join(inline(p) for p in abstract.split('\n\n'))
    tex=PREAMBLE+r'\phantomsection\section*{Abstract}\addcontentsline{toc}{section}{Abstract}'+'\n'+abstract_tex+'\n'
    tex+=r'''
\clearpage
\begingroup\setstretch{1}\fontsize{10.3}{12}\selectfont
\setlength{\cftbeforesecskip}{1pt}\setlength{\cftbeforesubsecskip}{0pt}
\tableofcontents
\endgroup
\clearpage
\begingroup\setstretch{1}\fontsize{10}{12.5}\selectfont
\phantomsection\addcontentsline{toc}{section}{List of tables}\listoftables
\clearpage
\phantomsection\addcontentsline{toc}{section}{List of figures}\listoffigures
\clearpage
\phantomsection\addcontentsline{toc}{section}{List of equations}\listofequations
\clearpage
\phantomsection\addcontentsline{toc}{section}{List of code listings}\listofcodelistings
\endgroup
'''
    tex+=parse_blocks(registers,front=True)
    tex+=r'\FloatBarrier\clearpage\pagenumbering{arabic}'+'\n'+parse_blocks(body)
    tex+=r'\FloatBarrier\clearpage\phantomsection\section*{References}\addcontentsline{toc}{section}{References}'+'\n'
    tex+=r'\begingroup\setstretch{1}\fontsize{10.5}{13.5}\selectfont'+'\n'
    tex+='\n\n'.join(r'\refentry{'+inline(r)+'}' for r in references)
    tex+='\n'+r'\endgroup'+'\n'+parse_blocks(appendix)+'\n'+r'\end{document}'+'\n'
    path=OUT/(NAME+'.tex');path.write_text(tex)
    shutil.copyfile(PAPER/'manuscript.md',OUT/'manuscript.md')
    shutil.copyfile(PAPER/'references-harvard.md',OUT/'references-harvard.md')
    shutil.copyfile(PAPER/'references.bib',OUT/'references.bib')
    if compile_pdf:
        for iteration in range(1,5):
            result=subprocess.run(['xelatex','-interaction=nonstopmode','-halt-on-error',NAME+'.tex'],cwd=OUT,capture_output=True,text=True)
            (OUT/f'compile-pass-{iteration}.txt').write_text(result.stdout+'\n'+result.stderr)
            if result.returncode:
                print(result.stdout[-7000:]);raise RuntimeError(f'XeLaTeX failed on pass {iteration}')
        print('Compiled:',OUT/(NAME+'.pdf'))
    print(json.dumps({'source':str(path),'references':len(references),'figures':16,'tables':27,'equations':30,'listings':15},indent=2))


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--no-compile',action='store_true')
    args=parser.parse_args();assemble(not args.no_compile)
