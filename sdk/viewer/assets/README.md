# Assets des Viewers

`DejaVuSans-viewer.ttf` ist eine Teilmenge von DejaVu Sans 2.37 (`dejavu-fonts-ttf-2.37`, Lizenz in `DejaVu-LICENSE.txt`). Sie enthält Latin-1, Pfeile, geometrische Formen und die Schachfiguren U+2654–U+265F. Der Build bettet sie in das Programm ein (E106).

Erzeugt mit fonttools:

```
pyftsubset DejaVuSans.ttf --unicodes="U+0020-007E,U+00A0-00FF,U+2010-2027,U+2190-21FF,U+2212,U+25A0-25FF,U+2654-265F,U+26A0,U+2713" --output-file=DejaVuSans-viewer.ttf
```
