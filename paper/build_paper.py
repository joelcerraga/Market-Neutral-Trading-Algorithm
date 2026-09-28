"""Refresh the manuscript and compile the author's final A4 portrait paper."""
from update_manuscript import assemble as update_manuscript
from assemble_final_paper import assemble as compile_paper


if __name__ == "__main__":
    update_manuscript()
    compile_paper()
