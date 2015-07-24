Setup

  $ export SHEET_FILE=$TMP/sheet-actions
  $ alias tim="$TESTDIR/../bin/timrun.py --no-color"

Running an unknown action

  $ tim almost-definitely-a-nonexistent-action
  I don't understand command 'almost-definitely-a-nonexistent-action'
  #self.filename: /home/matthias/Seafile/todo2/tim/tim-sheet.json

