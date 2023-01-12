import tkinter as tk

# pylint: disable=import-error
from src.gui.interfaces import LabelFrame, Frame
from src.common.interfaces import Configurable
from src.common import utils, settings
# pylint: enable=import-error

class Tolerance(LabelFrame):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, 'Tolerance Settings', **kwargs)

        self.displays = {}
        self.tolerance_settings = ToleranceSettings('tolerance')
        for key, value in self.tolerance_settings.config.items():
            self.update_global(key, value)
        self.create_edit_ui()

    def create_edit_ui(self):
        """
        Creates the frame for tolerance settings
        """
        self.displays = {}

        self.contents = Frame(self)
        self.contents.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=5, pady=5)
        for key, value in self.tolerance_settings.config.items():
            self.create_entry(key, value)
        self.focus()

        self.reset = tk.Button(self, text='Reset', command=self.reset_settings, takefocus=False)
        self.reset.pack(side=tk.LEFT, padx=5, pady=5)
        self.save = tk.Button(self, text='Save', command=self.save_settings, takefocus=False)
        self.save.pack(side=tk.RIGHT, padx=5, pady=5)

    def create_entry(self, key, value):
        """
        Create each entry in the table

        Args:
            key (string): name of the label
            value (float): value of the label
        """
        display_var = tk.StringVar(value=value)
        row = Frame(self.contents, highlightthickness=0)
        row.pack(expand=True, fill='x')
        label = tk.Entry(row)
        label.grid(row=0, column=0, sticky=tk.EW)
        label.insert(0, key)
        label.config(state=tk.DISABLED)
        def validate(val):
            """Entry must be float"""
            if isinstance(val, float):
                return True
            return False
        reg = (self.register(validate), '%d')
        entry = tk.Entry(row, textvariable=display_var,
                         validate='key', validatecommand=reg,
                         takefocus=False)
        entry.grid(row=0, column=1, sticky=tk.EW)
        self.displays[key] = display_var

    def reset_settings(self):
        """
        Resets the global and ToleranceSettings.config tolerance settings
        Resets the UI
        """
        settings.reset()
        self.tolerance_settings.set_config()
        self.tolerance_settings.save_config()
        self.refresh_ui()

    def destroy_contents(self):
        """
        Destroys the UI Frame
        """
        self.contents.destroy()
        self.reset.destroy()
        self.save.destroy()
    
    def refresh_ui(self):
        """
        Refreshes the values in the UI
        """
        self.destroy_contents()
        self.create_edit_ui()

    @utils.run_if_disabled('\n[!] Cannot save Tolerance Settings while Auto Maple is enabled')
    def save_settings(self):
        """
        Saves the global and ToleranceSettings.config tolerance settings
        """
        utils.print_separator()
        print(f"[~] Saving Tolerance Settings to '{self.tolerance_settings.TARGET}':")

        failures = 0
        for key, display_var in self.displays.items():
            try:
                value = float(display_var.get())
                self.tolerance_settings.set(key, value)
                self.update_global(key, value)
            except ValueError:
                print(f" !  '{key}' has to be a floating point number")
                failures += 1
                self.refresh_ui()
            except:
                print(f" !  '{key}' could not be saved")
                failures += 1
                self.refresh_ui()

        if failures == 0:
            self.tolerance_settings.save_config()
            print(' ~  Successfully saved all Tolerance Settings')
        else:
            print(' ~  Failed to save Tolerance Settings')

    def update_global(self, key, value):
        """
        Updates the global variable from GUI

        Args:
            key (string) : Name of the label
            value (float): Value for tolerance setting
        """
        if key == 'Move Tolerance':
            settings.move_tolerance = value
        if key == 'Adjust Tolerance':
            settings.adjust_tolerance = value


class ToleranceSettings(Configurable):
    DEFAULT_CONFIG = {
        'Move Tolerance': settings.move_tolerance,
        'Adjust Tolerance': settings.adjust_tolerance
    }
    
    global_mapping = {
        'Move Tolerance': 'move_tolerance',
        'Adjust Tolerance': 'adjust_tolerance'
    }
    def get(self, key):
        """
        Getter method
        """
        return self.config[key]

    def set(self, key, value):
        """
        Setter method
        """
        assert key in self.config
        self.config[key] = settings.SETTING_VALIDATORS[self.global_mapping[key]](value)

    def set_config(self):
        """
        Sets the ToleranceSettings.config to match the global variables
        """
        self.set('Move Tolerance', settings.move_tolerance)
        self.set('Adjust Tolerance', settings.adjust_tolerance)
