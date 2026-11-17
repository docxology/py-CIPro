# PDF layout

```latex
\usepackage{graphicx}
\usepackage[section]{placeins}
\usepackage{listings}
\usepackage{fancyhdr}
\lstset{basicstyle=\ttfamily\small,breaklines=true,columns=fullflexible}
\newtheorem{theorem}{Theorem}[section]
\newtheorem{remark}[theorem]{Remark}
\newtheorem{example}[theorem]{Example}

\definecolor{ciprolink}{HTML}{156568}
\definecolor{ciproquiet}{HTML}{3C596A}
\hypersetup{linkcolor=ciprolink,citecolor=ciprolink,urlcolor=ciprolink}
\setlength{\headheight}{14pt}
\setlength{\headsep}{13pt}
\pagestyle{fancy}
\fancyhf{}
\fancyhead[L]{\sffamily\footnotesize\bfseries\color{ciprolink} py-CIPro}
\fancyhead[R]{\sffamily\footnotesize\color{ciproquiet} Complete-intersection geometry}
\fancyfoot[R]{\sffamily\footnotesize\color{ciproquiet}\thepage}
\renewcommand{\headrulewidth}{0.25pt}
\renewcommand{\footrulewidth}{0pt}
\setcounter{tocdepth}{1}
\setcounter{topnumber}{3}
\setcounter{bottomnumber}{2}
\renewcommand{\topfraction}{0.90}
\renewcommand{\bottomfraction}{0.80}
\renewcommand{\textfraction}{0.08}
\renewcommand{\floatpagefraction}{0.82}
\setlength{\textfloatsep}{13pt plus 3pt minus 3pt}
\setlength{\LTcapwidth}{\textwidth}
\captionsetup{font=small,labelfont=bf}
\renewcommand{\bibfont}{\small}
\setlength{\bibsep}{3pt plus 1pt minus 1pt}
```
