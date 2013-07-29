# Only strip trailing whitespace from modified lines.

from difflib import SequenceMatcher

import sublime
import sublime_plugin

options = sublime.load_settings(
    'swenson_trim_trailing_whitespace.sublime-settings')
snapshots = {}

class TrimTrailingWhiteSpaceApplyCommand(sublime_plugin.TextCommand):
  def description(self):
    return "Trim trailing whitespace"


  def is_visible(self):
    return False


  def run(self, edit):
    view = self.view
    oldText = snapshots[view.id()]
    old = oldText.split('\n')
    new = view.substr(sublime.Region(0, view.size())).split('\n')
    # Remove the line numbers that were present before.
    new_lines = set(range(len(new)))
    sm = SequenceMatcher(None, old, new)
    for i, j, n in sm.get_matching_blocks():
      for k in range(j, j + n):
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
        # Note that we replace later in the file first, since we're changing
        # the number of characters in each line.
        for r, t in reversed(replacements):
          view.replace(edit, r, t)

    # Trim all whitespace on my files.
    patterns = options.get('owner_patterns', [])
    if any(view.find(pattern, 0, sublime.IGNORECASE) for pattern in patterns):
      trailing_white_space = view.find_all("[\t ]+$")
      if trailing_white_space:
        for r in reversed(trailing_white_space):
          view.erase(edit, r)


class TrimTrailingWhiteSpace(sublime_plugin.EventListener):
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
    view.run_command("trim_trailing_white_space_apply", dict())


  # Reload the file into the snapshot after saving.
  def on_post_save(self, view):
    self.on_load(view)

