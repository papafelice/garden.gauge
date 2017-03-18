#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4 nu

'''
    Gauge
    =====

    The :class:`Gauge` widget is a widget for displaying various gauges
    constisting of a stack of png images:
    (from bottom to top in a common folder)
      fond  cadran  aiguille(s)  bandeau
    Image file names have encoded (delimiter is _) the size, range, anchor point
    etc in order to ease to design of a custom gauge without recoding:
    Background:  fond_PX_PY          where PX and PY are the coordinates of then
                                     anchor point of the gauge, the size of the
                                     background determines the size of the gauge
    Front:       bandeauTYPE_SA_EA   where TYPE is an type name (default: Std)
                                     and SA and EA are the start and end angle
                                     of the usable area in degrees (0=top)
    Dial:        cadranSAEA_SV_EV    where SAEA must fit the values of the front
                                     and SV and EV are the start and end values
    Needle:      aiguilleTYPE_AX_AY  where TYPE is a type name (default: Std)
                                     and AX and AY are the coordinates of the
                                     anchor point of the needle
    The images should be white or light gray in order to use the color properly
    Images are searched for in the app folder, then in the __init__ folder

.. note::

Class extended by Felix Huber
Source svg files provided for customizing.

'''


__all__ = ('Gauge',)

__title__ = 'garden.gauge'
__version__ = '0.3'
__author__ = 'julien@hautefeuille.eu'

import kivy
kivy.require('1.9.0')
from math import radians
from kivy.app import App
from kivy.vector import Vector
from kivy.properties import NumericProperty
from kivy.properties import StringProperty
from kivy.properties import BoundedNumericProperty
from kivy.properties import VariableListProperty
from kivy.properties import ReferenceListProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.widget import Widget
from kivy.uix.scatter import Scatter
from kivy.uix.image import Image
from kivy.uix.label import Label
from kivy.uix.stencilview import StencilView
from kivy.graphics.transformation import Matrix
import sys
import os
import inspect
import glob
import struct


def get_fileconfig(filename):
    '''
    extract config (anchor position etc) from filename
    '''
    name = os.path.splitext(os.path.basename(filename))[0]
    ax = int(name.split("_", 3)[1])
    ay = int(name.split("_", 3)[2])
    return (ax, ay)


def get_png_size(filename):
    '''
    get size of png image from file
    '''

    with open(filename, 'rb') as f:
        data = f.read(24)
        if (data[:8] == '\211PNG\r\n\032\n') and (data[12:16] == 'IHDR'):
            w, h = struct.unpack('>LL', data[16:24])
            width = int(w)
            height = int(h)
        else:
            width, height = (100, 100)
    return (width, height)


class Needle(Scatter):
    '''
    A class to rotate and display a meter needle with an arbitrary anchor point
    and mouse dragging
    '''

    dragged = NumericProperty(0)

    def __init__(self, filename=None, color=[1, 1, 1, 1],
                 anchor=(0, 0), do_drag=False, **kwargs):
        size = get_png_size(filename)
        super(Needle, self).__init__(size=size, do_rotation=False,
                                     do_scale=False, do_translation=False,
                                     **kwargs)

        a = get_fileconfig(filename)
        self.anchor = (a[0], a[1])
        self.x = anchor[0] - a[0]
        self.y = anchor[1] - a[1]
        self._rotation = 0
        self.do_drag = do_drag

        self._img_needle = Image(size=size, source=filename, color=color)
        self.add_widget(self._img_needle)

    def _set_rotation(self, value):
        '''
        Turn needle by value degrees
        Note: this must access the private function of scatter
        in order to override the anchor and is not portable
        '''
        angle_change = self._rotation - value
        self._rotation = value
        r = Matrix().rotate(-radians(angle_change), 0, 0, 1)
        self.apply_transform(r, post_multiply=True, anchor=self.anchor)

    def setcolor(self, color):
        '''
        Set needle color
        '''
        self._img_needle.color = color

    def on_touch_down(self, touch):
        if self.do_drag is True:
            if self.collide_point(*touch.pos):
                touch.grab(self)
                return True
        return super(Needle, self).on_touch_down(touch)

    def on_touch_up(self, touch):
        if touch.grab_current is self:
            touch.ungrab(self)
        return super(Needle, self).on_touch_up(touch)

    def on_touch_move(self, touch):
        if not touch.grab_current is self:
            return False

        t = self.to_local(*touch.pos)
        rx, ry = t[0] - self.anchor[0], t[1] - self.anchor[1]
        angle = Vector(rx, ry).angle((0, 1))
        if angle > 90:
            angle = 90
        if angle < -90:
            angle = -90
        self.dragged = -angle
        return True


class Gauge(Widget):
    '''
    class to display a gauge with up to two needles
    '''

    gauge_color    = VariableListProperty([0.1, 0.1, 0.1, 1])
    dial_color     = VariableListProperty([1, 1, 1, 1])
    front_color    = VariableListProperty([1, 1, 1, 1])
    label_1_color  = VariableListProperty([0.5, 0.5, 0.5, 1])
    label_2_color  = VariableListProperty([0.5, 0.5, 0.5, 1])
    needle_1_color = VariableListProperty([1, 1, 1, 1])
    needle_2_color = VariableListProperty([1, 1, 1, 1])
    label_1_size   = NumericProperty(15)
    label_2_size   = NumericProperty(15)
    label_1_format = StringProperty("[b]{0:.0f}[/b]")
    label_2_format = StringProperty("[b]{0:.0f}[/b]")
    gauge_type     = StringProperty("ROUND")
    needle_1_type  = StringProperty("Std")
    needle_2_type  = StringProperty("None")
    front_type     = StringProperty("Std")
    gauge_min      = NumericProperty(0)
    gauge_max      = NumericProperty(100)
    value_1        = BoundedNumericProperty(0, min=0.0, max=100.0, errorvalue=0)
    value_2        = BoundedNumericProperty(0, min=0.0, max=100.0, errorvalue=0)
    dragged_1      = NumericProperty(0)
    dragged_2      = NumericProperty(0)
    scale          = NumericProperty(1.0)
    x              = NumericProperty(0)
    y              = NumericProperty(0)
    pos            = ReferenceListProperty(x, y)

    def __init__(self, do_drag_1=None, do_drag_2=None, **kwargs):
        super(Gauge, self).__init__(**kwargs)

        path = os.path.join(os.path.dirname(sys.argv[0]), self.gauge_type)
        if os.path.isdir(path) is not True:
            path = os.path.join(os.path.dirname(__file__) or '.',
                                self.gauge_type)

        file_fond = glob.glob(os.path.join(path, "fond_*.png"))[0]
        file_front = glob.glob(os.path.join(path, "bandeau" +
                                            self.front_type + "_*.png"))[0]
        self.angles = get_fileconfig(file_front)
        file_dial = glob.glob(os.path.join(path, "cadran" +
                                           str(self.angles[0]) +
                                           str(self.angles[1]) + "_*.png"))[0]

        ranges = get_fileconfig(file_dial)
        self.gauge_min = ranges[0]
        self.gauge_max = ranges[1]
        self.property('value_1').set_min(self, self.gauge_min)
        self.property('value_2').set_min(self, self.gauge_min)
        self.property('value_1').set_max(self, self.gauge_max)
        self.property('value_2').set_max(self, self.gauge_max)
        self.unit = float(self.angles[1] - self.angles[0]) / float(ranges[1] - ranges[0])
        size_gauge = get_png_size(file_fond)

        self._img_gauge = Image(source=file_fond, size=size_gauge,
                                color=self.gauge_color)
        self._img_dial = Image(source=file_dial, size=size_gauge,
                               color=self.dial_color)
        self._img_front = Image(source=file_front, size=size_gauge,
                                color=self.front_color)

        self._gauge = Scatter(size=size_gauge, do_rotation=False,
                              do_scale=True, do_translation=True)
        self._gauge.add_widget(self._img_gauge)
        self._gauge.add_widget(self._img_dial)

        if (self.needle_1_type) is not "None":
            self._glab_1 = Label(font_size=self.label_1_size,
                                 color=self.label_1_color,
                                 markup=True)
            self._glab_1.center_x = self._gauge.center_x
            self._glab_1.center_y = self._gauge.center_y - (size_gauge[1] / 6)
            self._gauge.add_widget(self._glab_1)
        else:
            self._glab_1 = None
        if (self.needle_2_type) is not "None":
            self._glab_2 = Label(font_size=self.label_2_size,
                                 color=self.label_2_color,
                                 markup=True)
            self._glab_2.center_x = self._gauge.center_x
            self._glab_2.center_y = self._gauge.center_y - (size_gauge[1] / 6) - self.label_1_size
            self._gauge.add_widget(self._glab_2)
        else:
            self._glab_2 = None

        self._stencil = StencilView(size=size_gauge)
        if (self.needle_1_type) is not "None":
            file_needle = glob.glob(os.path.join(path, "aiguille" +
                                                 self.needle_1_type +
                                                 "_*.png"))[0]
            self._needle_1 = Needle(filename=file_needle,
                                    color=self.needle_1_color,
                                    anchor=get_fileconfig(file_fond),
                                    do_drag=do_drag_1)
            self._stencil.add_widget(self._needle_1)
            self._needle_1.bind(dragged=self._dragged_1)
        else:
            self._needle_2 = None
        if (self.needle_2_type) is not "None":
            file_needle = glob.glob(os.path.join(path, "aiguille" +
                                                 self.needle_2_type +
                                                 "_*.png"))[0]
            self._needle_2 = Needle(filename=file_needle,
                                    color=self.needle_2_color,
                                    anchor=get_fileconfig(file_fond),
                                    do_drag=do_drag_2)
            self._stencil.add_widget(self._needle_2)
            self._needle_2.bind(dragged=self._dragged_2)
        else:
            self._needle_2 = None
        self._gauge.add_widget(self._stencil)

        self._gauge.add_widget(self._img_front)
        self.add_widget(self._gauge)

        self.bind(value_1=self._turn_1)
        self.bind(value_2=self._turn_2)
        self.bind(needle_1_color=self._needle_color_1)
        self.bind(needle_2_color=self._needle_color_2)
        self.bind(label_1_color=self._label_1)
        self.bind(label_2_color=self._label_2)

        self._turn_1()
        self._turn_2()

    def _turn_1(self, *args):
        '''
        Turn needle 1, 1 marker = 1 unit

        '''
        if self._needle_1 is not None:
            self._needle_1._set_rotation(- self.angles[0]
                                         - (self.value_1 - self.gauge_min) * self.unit)
            self._glab_1.text = self.label_1_format.format(self.value_1)

    def _turn_2(self, *args):
        '''
        Turn needle 2, 1 marker = 1 unit

        '''
        if self._needle_2 is not None:
            self._needle_2._set_rotation(- self.angles[0]
                                         - (self.value_2 - self.gauge_min) * self.unit)
            self._glab_2.text = self.label_2_format.format(self.value_2)

    def _dragged_1(self, *args):
        '''
        drag needle 1
        '''
        self.dragged_1 = self._needle_1.dragged / self.unit

    def _dragged_2(self, *args):
        '''
        drag needle 2
        '''
        self.dragged_2 = self._needle_2.dragged / self.unit

    def _needle_color_1(self, *args):
        '''
        Set needle 1 color
        '''
        if self._needle_1 is not None:
            self._needle_1.setcolor(self.needle_1_color)

    def _needle_color_2(self, *args):
        '''
        Set needle 2 color
        '''
        if self._needle_2 is not None:
            self._needle_2.setcolor(self.needle_2_color)

    def _label_1(self, *args):
        '''
        Set label 1 color
        '''
        if self._glab_1 is not None:
            self._glab_1.color = self.label_1_color

    def _label_2(self, *args):
        '''
        Set label 2 color
        '''
        if self._glab_2 is not None:
            self._glab_2.color = self.label_2_color


class GaugeApp(App):
    '''
    Demo for gauge class
    '''

    def build(self):
        from kivy.uix.slider import Slider

        def setgauge1(sender, value):
            mygauge1.value_1 = value
            mygauge3.value_1 = value / 50. * 120.
            mygauge5.value_1 = value / 50. * 145.
            mygauge6.value_1 = value / 50. * 290.

        def setgauge2(sender, value):
            mygauge2.value_1 = value
            mygauge5.value_2 = value / 50. * 111.
            mygauge6.value_2 = value / 50. * 222.

        def setgauge23(sender, value):
            mygauge3.value_2 = value / 50. * 120. / 2 * 43. / 50.
            if value < 40:
                mygauge3.needle_2_color = [0, 1, 0, 0.9]
                mygauge3.label_2_color = [0.5, 0.5, 0.5, 1]
            elif value < 75:
                mygauge3.needle_2_color = [1, 0.66, 0.0, 0.9]
                mygauge3.label_2_color = [0.5, 0.5, 0.5, 1]
            else:
                mygauge3.needle_2_color = [1, 0, 0, 0.9]
                mygauge3.label_2_color = [1, 0, 0, 1]

        def draggauge5(sender, dragged_1):
            sl1.value = sl1.value + dragged_1 * 50. / 145.

        boxH = BoxLayout(orientation='horizontal')
        mygauge1 = Gauge(gauge_type="RECT",
                         value=0, size_text=15,
                         label_1_format="[b]{0:.0f}[/b] Watt - Left",
                         gauge_color=[1, 1, 1, 1],
                         dial_color=[0.1, 0.1, 0.1, 1],
                         needle_1_color=[1, 0, 0, 1])
        mygauge2 = Gauge(gauge_type="RECT",
                         value=0, size_text=15,
                         label_1_format="[b]{0:.0f}[/b] Watt - Right",
                         gauge_color=[1, 1, 1, 1],
                         dial_color=[0.1, 0.1, 0.1, 1],
                         needle_1_color=[0, 1, 0, 1])

        mygauge3 = Gauge(gauge_type="ROUND",
                         needle_2_type="Skull",
                         front_type="Glass",
                         value=0, size_text=15,
                         label_1_format="[b]{0:.0f}[/b] Å/s[sup]2[/sup]",
                         label_2_format="[b]{0:.0f}[/b] x10 Å/s[sup]2[/sup]",
                         gauge_color=[0.1, 0.1, 0.1, 1],
                         dial_color=[1, 1, 1, 1],
                         needle_1_color=[1, 1, 1, 1],
                         needle_2_color=[0, 1, 0, 0.9])
        mygauge5 = Gauge(gauge_type="ELE",
                         needle_2_type="Antenna",
                         front_type="Antenna",
                         value=0, size_text=15,
                         label_1_format="[b]{0:.1f}[/b]°",
                         label_2_format="[b]{0:.1f}[/b]°",
                         gauge_color=[1, 1, 1, 1],
                         label_1_color=[0, 1, 0, 1],
                         label_2_color=[1, 0, 0, 1],
                         do_drag_1=True)
        mygauge6 = Gauge(gauge_type="AZI",
                         needle_2_type="Antenna",
                         front_type="Std",
                         value=0, size_text=15,
                         label_1_format="[b]{0:.1f}[/b]°",
                         label_2_format="[b]{0:.1f}[/b]°",
                         gauge_color=[1, 1, 1, 1],
                         label_1_color=[0, 1, 0, 1],
                         label_2_color=[1, 0, 0, 1])

        sl1 = Slider(orientation='vertical', min=0, max=50, errorvalue=25)
        sl2 = Slider(orientation='vertical', min=0, max=50, errorvalue=25)
        sl1.bind(value=setgauge1)
        sl2.bind(value=setgauge2)
        sl2.bind(value=setgauge23)
        mygauge5.bind(dragged_1=draggauge5)
        boxH.add_widget(mygauge1)
        boxH.add_widget(mygauge2)
        boxH.add_widget(mygauge3)
        boxH.add_widget(mygauge5)
        boxH.add_widget(mygauge6)
        boxH.add_widget(sl1)
        boxH.add_widget(sl2)

        mygauge1._gauge.pos = (0, 0)
        mygauge2._gauge.pos = (256, 0)
        mygauge3._gauge.pos = (256 - 128 * 1.2, 400)
        mygauge3._gauge.scale = 1.2
        mygauge5._gauge.pos = (0, 128)
        mygauge6._gauge.pos = (256, 128)

        return boxH

if __name__ == '__main__':
    GaugeApp().run()
