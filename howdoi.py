import functools
import os
import platform

import sublime
import sublime_plugin

from async_exec import AsyncProcess, ProcessListener


PLATFORM = platform.system()
PLATFORM_IS_WINDOWS = PLATFORM is 'Windows'


MISSING_EXECUTABLE_ERROR_MSG = """
Couldn't run the `howdoi` command (%s).

This can mean two things:

1. You don't have `howdoi` installed. Run `sudo pip install howdoi`
2. You have not set a correct value for `howdoi_path` in the settings file (Preferences > Package Settings > howdoi).

If it still doesn't work, feel free to create an issue here:
https://github.com/surjikal/sublime-howdoi
"""


UNHANDLED_EXCEPTION_ERROR_MSG = """
Unhandled exception while trying to run the `howdoi` command:

%s

Please open an issue report here:
https://github.com/surjikal/sublime-howdoi

Sorry about that!
"""


class PromptHowdoiCommand(sublime_plugin.WindowCommand, ProcessListener):

    SETTINGS = sublime.load_settings("howdoi.sublime-settings")


    def run(self):
        self.window.show_input_panel('howdoi>', '', self.on_prompt_done, None, None)


    def on_prompt_done(self, text):
        sublime.status_message("Fetching answer...")
        print "[howdoi] Fetching answer for query '%s'." % text
        try:
            self.run_howdoi(text)
        except OSError as e:
            self.write_to_panel(MISSING_EXECUTABLE_ERROR_MSG % str(e))
        except Exception as e:
             self.write_to_panel(UNHANDLED_EXCEPTION_ERROR_MSG % str(e))


    def on_data(self, proc, data):
        print "[howdoi] Data: %s" % data
        sublime.set_timeout(functools.partial(self.write_to_panel, data), 0)


    def on_finished(self, proc):
        print "[howdoi] Finished."
        sublime.set_timeout((lambda: sublime.status_message("Done!")), 0)


    def write_to_panel(self, text):
        active_view = self.window.active_view()

        if not active_view:
            print '[howdoi] No active view.'
            return

        active_view.run_command('write_to_panel', {
            'name': 'howdoi_output',
            'text': text
        })


    def run_howdoi(self, query,  position=1, display_link_only=False, display_full_answer=False):
        args = ['howdoi', query]
        path = self.SETTINGS.get('howdoi_path')
        return self._execute_program(args, path)


    def _execute_program(self, args, path):
        if path and PLATFORM_IS_WINDOWS:
            os.environ['PATH'] = path
            path = None

        env = {'PATH': path} if path else None
        return AsyncProcess(args, env, self)



class WriteToPanelCommand(sublime_plugin.TextCommand):

    def run(self, edit, name, text):
        window = self.view.window()
        self.write_to_panel(window, name, text)

    def write_to_panel(self, window, name, text):
        panel = window.get_output_panel(name)

        text = text.decode('utf8')
        panel.set_read_only(False)
        edit = panel.begin_edit()
        panel.insert(edit, 0, text)
        panel.end_edit(edit)
        panel.sel().clear()
        panel.set_read_only(True)

        window.run_command('show_panel', {'panel': 'output.%s' % name})

