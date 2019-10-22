import re

punctuation_interfix = re.compile(r"[“”?!:;,.…\-–—~/•]")
punctuation_infix = re.compile(r"['’‘]")
possession = re.compile(r"['’‘]s\b")
