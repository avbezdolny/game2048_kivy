#!python3
# -*- coding: utf-8 -*-

import kivy
kivy.require('1.11.1')

from kivy.app import App
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.core.window import Keyboard
from kivy.core.audio import SoundLoader
from kivy.utils import get_color_from_hex, platform
from kivy.uix.widget import Widget
from kivy.animation import Animation
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.image import Image
from kivy.properties import ObjectProperty, DictProperty, ListProperty, NumericProperty, StringProperty, BooleanProperty
from kivy.uix.modalview import ModalView
from kivy.storage.dictstore import DictStore
from os.path import join, dirname
import random
import math
import sys


# Returns path containing content - either locally or in pyinstaller tmp file
def resourcePath():
    if hasattr(sys, '_MEIPASS'):
        return join(sys._MEIPASS)
    return join(dirname(__file__))


class Board(Widget):
    trace = BooleanProperty(False)

    def on_touch_down(self, touch):
        if not App.get_running_app().block:
            self.trace = True

    def on_touch_move(self, touch):
        if self.trace and not App.get_running_app().block:
            touch_path = min(Window.width, Window.height) / 24
            if math.fabs(touch.dpos[0]) >= touch_path or math.fabs(touch.dpos[1]) >= touch_path:
                if math.fabs(touch.dpos[0]) > math.fabs(touch.dpos[1]):
                    if touch.dpos[0] < 0 and touch.pos[0] < Window.width * 0.75:
                        self.trace = False
                        App.get_running_app().move(-1, 0)
                    elif touch.dpos[0] > 0 and touch.pos[0] > Window.width * 0.25:
                        self.trace = False
                        App.get_running_app().move(1, 0)
                elif math.fabs(touch.dpos[1]) > math.fabs(touch.dpos[0]):
                    if touch.dpos[1] < 0 and touch.pos[1] < Window.height * 0.75:
                        self.trace = False
                        App.get_running_app().move(0, -1)
                    elif touch.dpos[1] > 0 and touch.pos[1] > Window.height * 0.25:
                        self.trace = False
                        App.get_running_app().move(0, 1)

    def on_touch_up(self, touch):
        self.trace = False


class Cell(Widget):
    pass


class Tile(Widget):
    number = NumericProperty(2)
    number_new = NumericProperty(2)
    check = BooleanProperty(False)

    shadow_colors = {
        2: '#c62828',
        4: '#1565c0',
        8: '#2e7d32',
        16: '#ff8f00',
        32: '#ad1457',
        64: '#283593',
        128: '#00695c',
        256: '#ef6c00',
        512: '#931212',
        1024: '#0b3b86',
        2048: '#154819',
        4096: '#d84315',
        8192: '#6a093d',
        16384: '#131a5f',
        32768: '#00342b',
        65536: '#be3a11',
        131072: '#32211d'
    }


class Btn(ButtonBehavior, Widget):
    text = StringProperty('btn')

    def __init__(self, **kwargs):
        super(Btn, self).__init__(**kwargs)


class SoundBtn(ButtonBehavior, Image):
    shadow_color = ListProperty(get_color_from_hex('#42424200'))

    def __init__(self, **kwargs):
        super(SoundBtn, self).__init__(**kwargs)


class ViewChoice(Widget):
    text = StringProperty('...')


class ViewInfo(Widget):
    text = StringProperty('...')


class Game2048App(App):
    if platform in ['win', 'linux', 'mac']:
        icon = 'data/icon.png'
        title = '2048'
        #Window.clearcolor = get_color_from_hex('#616161')
        Window.size = (480, 800)
        Window.left = 100
        Window.top = 100

    board = ObjectProperty()
    cell_size = ListProperty([100, 100])
    score = NumericProperty(0)
    best = NumericProperty(0)
    step = NumericProperty(0)
    savepoint = NumericProperty(0)
    savepoint_score = NumericProperty(0)
    savepoint_step = NumericProperty(0)
    check_savepoint = BooleanProperty(False)
    block = BooleanProperty(True)
    moving = BooleanProperty(False)
    game_over = BooleanProperty(False)
    key_vectors = DictProperty()
    tiles = None
    remove_tiles = None
    savepoint_tiles = None
    store = None
    view_exit = None
    view_info = None
    view_new = None
    view_gameover = None
    view_update = None
    view_savepoint = None

    is_sound = BooleanProperty(True)
    sound_click = None
    sound_popup = None
    sound_move  = None

    def on_start(self):
        self.board = self.root.ids.board

        self.key_vectors = {
            Keyboard.keycodes['up']: (0, 1),
            Keyboard.keycodes['right']: (1, 0),
            Keyboard.keycodes['down']: (0, -1),
            Keyboard.keycodes['left']: (-1, 0),
        }

        # tiles
        self.cell_size = [(self.board.width - 3 * self.board.width / 40) / 4] * 2
        self.tiles = [[None for i in range(4)] for j in range(4)]
        self.remove_tiles = [[None for i in range(4)] for j in range(4)]

        # sounds
        self.sound_click = SoundLoader.load('click.wav')
        self.sound_popup = SoundLoader.load('popup.wav')
        self.sound_move  = SoundLoader.load('click.wav')

        # exit dialog
        self.view_exit = ModalView(size_hint=(None, None), size=[self.board.width, self.board.width * 0.75], auto_dismiss=False)
        self.view_exit.add_widget(ViewChoice(text='Exit the game?'))
        self.view_exit.children[0].ids.yes_btn.bind(on_release=self.stop)

        # info dialog
        self.view_info = ModalView(size_hint=(None, None), size=[self.board.width, self.board.width * 0.75], auto_dismiss=False)
        self.view_info.add_widget(ViewInfo(text='[size=' + str(int(min(self.view_info.width, self.view_info.height) / 14)) + ']GAME 2048[/size][size=' + str(int(min(self.view_info.width, self.view_info.height) / 20)) + ']\n\nSwipe to move the tiles. When two tiles with the same number touch, they merge into one. Get to the 2048 tile and reach a high score!\nBased by Gabriele Cirulli original game :)[/size][size=' + str(int(min(self.view_info.width, self.view_info.height) / 30)) + ']\n\n* * *\n(c) Anton Bezdolny, 2020 / ver. 1.1 /[/size]'))

        # new game dialog
        self.view_new = ModalView(size_hint=(None, None), size=[self.board.width, self.board.width * 0.75], auto_dismiss=False)
        self.view_new.add_widget(ViewChoice(text='Start new game?'))
        self.view_new.children[0].ids.yes_btn.bind(on_release=self.new_game)

        # game over dialog
        self.view_gameover = ModalView(size_hint=(None, None), size=[self.board.width, self.board.width * 0.75], auto_dismiss=False)
        self.view_gameover.add_widget(ViewInfo(text='* GAME OVER *'))

        # update savepoint dialog
        self.view_update = ModalView(size_hint=(None, None), size=[self.board.width, self.board.width * 0.75], auto_dismiss=False)
        self.view_update.add_widget(ViewInfo())

        # load savepoint dialog
        self.view_savepoint = ModalView(size_hint=(None, None), size=[self.board.width, self.board.width * 0.75], auto_dismiss=False)
        self.view_savepoint.add_widget(ViewChoice())
        self.view_savepoint.children[0].ids.yes_btn.bind(on_release=self.load_savepoint)
        self.view_savepoint.children[0].ids.no_btn.bind(on_release=self.pass_savepoint)

        # bind's
        Window.bind(on_key_down=self.on_key_down)
        self.board.bind(pos=Clock.schedule_once(self.resize, 0.150))

        # game start
        # load data settings
        if platform in ['win', 'linux', 'mac']:  # desktop
            self.store = DictStore(join(self.user_data_dir, 'store.dat'))
        else:  # if platform in ['android', 'ios']
            self.store = DictStore('store.dat')  # android API 26+ без запроса разрешений доступа
        if self.store.exists('matrix'):
            self.load_data()
        else:
            self.new_game()

    def cell_pos(self, row, col):
        return (self.board.x + self.cell_size[0] * row + row * self.board.width / 40, self.board.y + self.cell_size[0] * col + col * self.board.width / 40)

    def all_cells(self, flip_row=False, flip_col=False):
        for row in (reversed(range(4)) if flip_row else range(4)):
            for col in (reversed(range(4)) if flip_col else range(4)):
                yield (row, col)

    def valid_cell(self, row, col):
        return (row >= 0 and col >= 0 and row <= 3 and col <= 3)

    def can_move(self, row, col):
        return (self.valid_cell(row, col) and self.tiles[row][col] is None)

    def can_combine(self, row, col, number, check):
        return (self.valid_cell(row, col) and
                self.tiles[row][col] is not None and
                self.tiles[row][col].number_new == number and
                not self.tiles[row][col].check and
                not check)

    def count_value(self, value):  # counter same tiles
        i = 0
        for row, col in self.all_cells():
            if self.tiles[row][col] and self.tiles[row][col].number_new == value:
                i += 1
        return i

    def is_deadlocked(self):
        for row, col in self.all_cells():
            if self.tiles[row][col] is None:
                return False
            if self.can_combine(row + 1, col, self.tiles[row][col].number, self.tiles[row][col].check) or self.can_combine(row, col + 1, self.tiles[row][col].number, self.tiles[row][col].check):
                return False
        return True

    def on_key_down(self, window, key, *args):
        if key in self.key_vectors and not self.block:
            self.move(*self.key_vectors[key])
        elif key in [27, 4]:  # ESC and BACK_BUTTON
            self.view_exit.open()
            return True

    def save_data(self):
        matrix = [[None for i in range(4)] for j in range(4)]
        for row, col in self.all_cells():
            if self.tiles[row][col]:
                matrix[row][col] = self.tiles[row][col].number
        self.store.put('matrix', value=matrix)
        self.store.put('score', value=self.score)
        self.store.put('best', value=self.best)
        self.store.put('step', value=self.step)
        self.store.put('game_over', value=self.game_over)
        self.store.put('savepoint', value=self.savepoint)
        self.store.put('savepoint_score', value=self.savepoint_score)
        self.store.put('savepoint_step', value=self.savepoint_step)
        self.store.put('savepoint_matrix', value=self.savepoint_tiles)
        self.store.put('is_sound', value=self.is_sound)

    def load_data(self):
        self.score = self.store.get('score')['value']
        self.best = self.store.get('best')['value']
        self.step = self.store.get('step')['value']
        self.game_over = self.store.get('game_over')['value']
        self.savepoint = self.store.get('savepoint')['value']
        self.savepoint_score = self.store.get('savepoint_score')['value']
        self.savepoint_step = self.store.get('savepoint_step')['value']

        matrix = self.store.get('matrix')['value']
        for row, col in self.all_cells():
            if matrix[row][col]:
                tile = Tile(number=matrix[row][col], number_new=matrix[row][col], pos=self.cell_pos(row, col))
                self.tiles[row][col] = tile
                self.board.add_widget(tile)

        self.savepoint_tiles = self.store.get('savepoint_matrix')['value']
        self.is_sound = self.store.get('is_sound')['value']
        self.block = True if self.game_over else False

    def load_savepoint(self, *args):
        self.score = self.savepoint_score
        self.step = self.savepoint_step
        self.game_over = False

        for row, col in self.all_cells():
            if self.savepoint_tiles[row][col]:
                tile = Tile(number=self.savepoint_tiles[row][col], number_new=self.savepoint_tiles[row][col], pos=self.cell_pos(row, col))
                self.tiles[row][col] = tile
                self.board.add_widget(tile)

        self.block = False

    def pass_savepoint(self, *args):
        self.new_tile()
        self.new_tile()

    def new_game(self, *args):
        self.score = 0
        self.step = 0
        self.game_over = False
        self.moving = False
        self.check_savepoint = False
        self.block = True

        # clear old widget
        if self.tiles:
            for row, col in self.all_cells():
                remove_tile = self.tiles[row][col]
                if remove_tile:
                    self.board.remove_widget(remove_tile)
                    self.tiles[row][col] = None

        if self.savepoint > 0:
            self.view_savepoint.children[0].text = 'Load savepoint\n' + str(self.savepoint) + '?'
            self.view_savepoint.open()
        else:
            self.new_tile()
            self.new_tile()
            '''rnumb = 2
            for row, col in self.all_cells():  # TEST ALL TILE'S NUMBER !!!
                rnumb *= 2
                tile = Tile(number=rnumb, number_new=rnumb, pos=self.cell_pos(row, col))
                self.tiles[row][col] = tile
                self.board.add_widget(tile)'''

    def new_tile(self):
        empty_cells = [(row, col) for row, col in self.all_cells() if self.tiles[row][col] is None]
        row, col = random.choice(empty_cells)
        rnumb = (2 if random.randint(1, 100) <= 90 else 4)

        tile = Tile(number=rnumb, number_new=rnumb, pos=self.cell_pos(row, col))
        self.tiles[row][col] = tile
        self.board.add_widget(tile)

        # game analyze
        if len(empty_cells) == 1 and self.is_deadlocked():
            self.game_over = True
            Clock.schedule_once(self.after_game_over, 0.5)
        else:
            if self.check_savepoint:
                self.check_savepoint = False
                self.savepoint_score = self.score
                self.savepoint_step = self.step
                self.savepoint_tiles = [[None for i in range(4)] for j in range(4)]
                for r, c in self.all_cells():
                    if self.tiles[r][c]:
                        self.savepoint_tiles[r][c] = self.tiles[r][c].number
                self.view_update.children[0].text = 'New savepoint\n' + str(self.savepoint) + '!'
                Clock.schedule_once(self.after_update_savepoint, 0.5)

            self.block = False

    def after_game_over(self, *args):
        if self.is_sound and self.sound_popup: self.sound_popup.play()
        self.view_gameover.open()

    def after_update_savepoint(self, *args):
        if self.is_sound and self.sound_popup: self.sound_popup.play()
        self.view_update.open()

    def move(self, dir_x, dir_y):
        if not self.block:
            self.block = True

            for row, col in self.all_cells(dir_x > 0, dir_y > 0):
                tile = self.tiles[row][col]
                if not tile:
                    continue
                else:
                    x, y = row, col
                    while self.can_move(x + dir_x, y + dir_y):
                        self.tiles[x][y] = None
                        x += dir_x
                        y += dir_y
                        self.tiles[x][y] = tile

                    if self.can_combine(x + dir_x, y + dir_y, tile.number, tile.check):
                        self.tiles[x][y] = None
                        x += dir_x
                        y += dir_y
                        self.remove_tiles[x][y] = self.tiles[x][y]  # remove widget
                        self.tiles[x][y] = tile
                        tile.number_new *= 2
                        tile.check = True  # check this join numbers
                        self.score += tile.number_new

                        if self.score > self.best:  # best score
                            self.best = self.score

                        # savepoint
                        if tile.number_new >= 1024 and tile.number_new >= self.savepoint and self.count_value(tile.number_new) == 1:
                            self.check_savepoint = True
                            self.savepoint = tile.number_new

                    if x == row and y == col:
                        continue  # nothing has happened

                    anim = Animation(pos=self.cell_pos(x, y), duration=0.2, transition='linear')
                    anim.start(tile)
                    if not self.moving:
                        self.moving = True
                        anim.bind(on_complete=self.after_move)
                        if self.is_sound and self.sound_move: self.sound_move.play()
            # if no moves
            if not self.moving:
                self.block = False

    def after_move(self, *args):
        self.moving = False
        self.step += 1

        for row, col in self.all_cells():
            remove_tile = self.remove_tiles[row][col]
            if remove_tile:
                self.board.remove_widget(remove_tile)
                self.remove_tiles[row][col] = None

            tile = self.tiles[row][col]
            if tile:
                tile.number = tile.number_new
                tile.check = False

        self.new_tile()

    def resize(self, *args):
        self.cell_size = [(self.board.width - 3 * self.board.width / 40) / 4] * 2
        for row, col in self.all_cells():
            tile = self.tiles[row][col]
            if tile:
                anim = Animation(pos=self.cell_pos(row, col), duration=0.2, transition='linear')
                anim.start(tile)

        # dialog's
        self.view_exit.size = [self.board.width, self.board.width * 0.75]
        self.view_info.size = [self.board.width, self.board.width * 0.75]
        self.view_info.children[0].text = '[size=' + str(int(min(self.view_info.width, self.view_info.height) / 14)) + ']GAME 2048[/size][size=' + str(int(min(self.view_info.width, self.view_info.height) / 20)) + ']\n\nSwipe to move the tiles. When two tiles with the same number touch, they merge into one. Get to the 2048 tile and reach a high score!\nBased by Gabriele Cirulli original game :)[/size][size=' + str(int(min(self.view_info.width, self.view_info.height) / 30)) + ']\n\n* * *\n(c) Anton Bezdolny, 2020 / ver. 1.1 /[/size]'
        self.view_new.size = [self.board.width, self.board.width * 0.75]
        self.view_gameover.size = [self.board.width, self.board.width * 0.75]
        self.view_update.size = [self.board.width, self.board.width * 0.75]
        self.view_savepoint.size = [self.board.width, self.board.width * 0.75]

    def on_pause(self):
        self.save_data()
        return True

    def on_resume(self):
        pass

    def on_stop(self):
        self.save_data()
        sys.exit(0)  # for Android and other OS


if __name__ == '__main__':
    if platform in ['win', 'linux', 'mac']:  # desktop
        kivy.resources.resource_add_path(resourcePath())
    #Window.fullscreen = 'auto'
    Game2048App().run()
