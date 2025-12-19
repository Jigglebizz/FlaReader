import argparse
import sys
from pathlib import Path
from flafile import FlaFile
from view_fla import QtFlaWindow
from PyQt6.QtWidgets import QApplication

#------------------------------------------------------------------------------------------------
if __name__ == '__main__':
  def ParseArgs():
    parser = argparse.ArgumentParser()
    parser.add_argument( '--fla', help='Shows which projects contribute which DataFiles to the CodeGen project' )
    return parser.parse_args()
  args = ParseArgs()

  fla_path = Path( args.fla )
  if fla_path.exists():
    fla_file : FlaFile = FlaFile( fla_path )

    qt_app    : QApplication = QApplication( sys.argv )
    qt_window : QtFlaWindow = QtFlaWindow( fla_file )
    qt_window.show()
    sys.exit( qt_app.exec() )
