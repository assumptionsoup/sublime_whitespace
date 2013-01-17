# Only strip trailing whitespace from modified lines.
# (Unless I own the file.)
#
# I suggest you modify the patterns line below to include your own email
# addresses.
#
# Author: Christopher Swenson (chris@caswenson.com)


from difflib import SequenceMatcher

import sublime
import sublime_plugin

options = sublime.load_settings(
    'swenson_trim_trailing_whitespace.sublime-settings')
snapshots = {}

class SwensonTrimTrailingWhiteSpace(sublime_plugin.EventListener):
  # Load a snapshot of the file.
  def on_load(self, view):
    snapshots[view.id()] = view.substr(sublime.Region(0, view.size()))

  on_clone = on_load
  on_new = on_load

  def on_pre_save(self, view):
    # Trim whitespace on any new files.  Note that if we don't have any
    # snapshot, then either the plugin has failed or it's a new document.
    oldText = snapshots.get(view.id())
    if oldText is None:
      # We don't have a snapshot.  This is an exceptional case, so just put
      # the current contents as the snapshot and do nothing.
      snapshots[view.id()] = view.substr(sublime.Region(0, view.size()))
      return

    old = oldText.split('\n')
    new = view.substr(sublime.Region(0, view.size())).split('\n')
    # Remove the line numbers that were present before.
    new_lines = set(range(len(new)))
    sm = SequenceMatcher(None, old, new)
    for i, j, n in sm.get_matching_blocks():
      for k in xrange(j, j + n):
        new_lines.remove(k)
    # Trim the whitespace on the new lines:
    if new_lines:
      replacements = []

      for line_no in new_lines:
        pt = view.text_point(line_no, 0)
        old_line = view.line(pt)
        old_line_text = view.substr(old_line)
        new_line_text = old_line_text.rstrip()
        if old_line_text != new_line_text:
          # Only add it if it actually changed, to prevent shifting e.g.
          # the cursor on already groomed lines
          replacements.append((old_line, new_line_text))

      if replacements:
        edit = view.begin_edit()
        # Note that we replace later in the file first, since we're changing
        # the number of characters in each line.
        for old_line, new_line_text in reversed(replacements):
          view.replace(edit, old_line, new_line_text)
        view.end_edit(edit)

    # Trim all whitespace on my files.
    patterns = options.get('owner_patterns', [])
    if any(view.find(pattern, 0, sublime.IGNORECASE) for pattern in patterns):
      trailing_white_space = view.find_all("[\t ]+$")
      if trailing_white_space:
        trailing_white_space.reverse()
        edit = view.begin_edit()
        for r in trailing_white_space:
            view.erase(edit, r)
        view.end_edit(edit)

  # Reload the file into the snapshot after saving.
  def on_post_save(self, view):
    self.on_load(view)
