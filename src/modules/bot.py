"""An interpreter that reads and executes user-created routines."""

import threading
import time
import inspect
import importlib
import traceback
from os.path import splitext, basename, join
from datetime import datetime

import git
import cv2

# pylint: disable=import-error
from src.common import config, utils
from src.detection import detection
from src.routine import components
from src.routine.routine import Routine
from src.command_book.command_book import CommandBook
from src.routine.components import Point
from src.common.vkeys import press, click
from src.common.interfaces import Configurable
# pylint: enable=import-error

# The rune's buff icon
RUNE_BUFF_TEMPLATE = cv2.imread('assets/rune_buff_template.jpg', 0)
PRELOAD_FRAME = cv2.imread('assets/rune_buff_template.jpg')

class Bot(Configurable):
    """A class that interprets and executes user-defined routines."""

    DEFAULT_CONFIG = {
        'Interact': 'n',
        'Feed pet': '9'
    }

    def __init__(self):
        """Loads a user-defined routine on start up and initializes this Bot's main thread."""

        super().__init__('keybindings')
        config.bot = self

        self.rune_active = False
        self.solve_rune_success = True
        self.rune_pos = (0, 0)
        self.rune_closest_pos = (0, 0)      # Location of the Point closest to rune
        self.submodules = []
        self.command_book = None            # CommandBook instance

        config.routine = Routine()

        self.ready = False
        self.thread = threading.Thread(target=self._main)
        self.thread.daemon = True

    def start(self):
        """
        Starts this Bot object's thread.
        :return:    None
        """

        # self.update_submodules()
        print('\n[~] Started main bot loop')
        self.thread.start()

    def _main(self):
        """
        The main body of Bot that executes the user's routine.
        :return:    None
        """

        print('\n[~] Initializing detection algorithm:\n')
        model = detection.load_model()
        detection.preload_cudnn(model, PRELOAD_FRAME)
        print('\n[~] Initialized detection algorithm')

        self.ready = True
        config.listener.enabled = True
        last_fed = time.time()
        while True:
            if config.enabled and len(config.routine) > 0:
                # Buff and feed pets
                self.command_book.buff.main()
                pet_settings = config.gui.settings.pets
                auto_feed = pet_settings.auto_feed.get()
                num_pets = pet_settings.num_pets.get()
                now = time.time()
                if auto_feed and now - last_fed > 1200 / num_pets:
                    press(self.config['Feed pet'], 1)
                    last_fed = now

                # Highlight the current Point
                config.gui.view.routine.select(config.routine.index)
                config.gui.view.details.display_info(config.routine.index)

                # Execute next Point in the routine
                element = config.routine[config.routine.index]
                if self.rune_active and isinstance(element, Point) \
                        and element.location == self.rune_closest_pos:
                    self._solve_rune(model)
                element.execute()
                config.routine.step()
            else:
                time.sleep(0.01)

    @utils.run_if_enabled
    def _solve_rune(self, model):
        """
        Moves to the position of the rune and solves the arrow-key puzzle.
        :param model:   The TensorFlow model to classify with.
        :param sct:     The mss instance object with which to take screenshots.
        :return:        None
        """

        move = self.command_book['move']
        move(*self.rune_pos).execute()
        adjust = self.command_book['adjust']
        adjust(*self.rune_pos).execute()
        time.sleep(0.2)
        press(self.config['Interact'], 1, down_time=0.2)        # Inherited from Configurable

        print('\nSolving rune:')
        inferences = []
        fail_count = 0
        for _ in range(15):
            if fail_count < 2:
                frame = config.capture.frame
                solution = detection.merge_detection(model, frame)
                if solution:
                    print(', '.join(solution))
                    if solution in inferences:
                        print('Solution found, entering result')
                        self.enter_solution(solution)
                        self.solve_rune_success = True
                        break
                    elif len(solution) == 4:
                        inferences.append(solution)
                    else:
                        fail_count += 1
            else:
                self.solve_rune_success = False
                break
        
        if not self.solve_rune_success:
            config.telegram.waiting_response = True
            dir_path = join('assets','video')
            video_name = datetime.utcnow().strftime('%Y-%m-%d_%H-%M-%S-%f')[:-3] + '.mp4'
            path_for_video = join(dir_path, video_name)
             # Send Telegram video
            duration = 1.5
            config.capture.record_rune(path_for_video, duration=duration)
            time.sleep(duration)
            config.telegram.send_rune_video(path_for_video)
            now = time.time()
            while time.time()-now < (12-duration):
                if len(config.telegram.manual_replies) == 4:
                    self.enter_solution(config.telegram.manual_replies)
                    self.solve_rune_success = True
                    break
            config.telegram.waiting_response = False
            config.telegram.manual_replies.clear()

    def load_commands(self, file):
        """
        todo
        """
        try:
            self.command_book = CommandBook(file)
            config.gui.settings.update_class_bindings()
        except ValueError:
            pass    # TODO: UI warning popup, say check cmd for errors

    def enter_solution(self, solution):
        for arrow in solution:
            press(arrow, 1, down_time=0.1)
        time.sleep(1)
        for _ in range(3):
            time.sleep(0.3)
            frame = config.capture.frame
            rune_buff = utils.multi_match(frame[:frame.shape[0] // 8, :],
                                          RUNE_BUFF_TEMPLATE,
                                          threshold=0.9)
            if rune_buff:
                rune_buff_pos = min(rune_buff, key=lambda p: p[0])
                target = (
                    round(rune_buff_pos[0] + config.capture.window['left']),
                    round(rune_buff_pos[1] + config.capture.window['top'])
                )
                click(target, button='right')
        self.rune_active = False
    
    def update_submodules(self, force=False):
        """
        Pulls updates from the submodule repositories. If FORCE is True,
        rebuilds submodules by overwriting all local changes.
        """

        utils.print_separator()
        print('[~] Retrieving latest submodules:')
        self.submodules = []
        repo = git.Repo.init()
        with open('.gitmodules', 'r', encoding="utf8") as file:
            lines = file.readlines()
            i = 0
            while i < len(lines):
                if lines[i].startswith('[') and i < len(lines) - 2:
                    path = lines[i + 1].split('=')[1].strip()
                    url = lines[i + 2].split('=')[1].strip()
                    self.submodules.append(path)
                    try:
                        repo.git.clone(url, path)       # First time loading submodule
                        print(f" -  Initialized submodule '{path}'")
                    except git.exc.GitCommandError:
                        sub_repo = git.Repo(path)
                        if not force:
                            sub_repo.git.stash()        # Save modified content
                        sub_repo.git.fetch('origin', 'main')
                        sub_repo.git.reset('--hard', 'FETCH_HEAD')
                        if not force:
                            try:                # Restore modified content
                                sub_repo.git.checkout('stash', '--', '.')
                                print(f" -  Updated submodule '{path}', restored local changes")
                            except git.exc.GitCommandError:
                                print(f" -  Updated submodule '{path}'")
                        else:
                            print(f" -  Rebuilt submodule '{path}'")
                        sub_repo.git.stash('clear')
                    i += 3
                else:
                    i += 1
