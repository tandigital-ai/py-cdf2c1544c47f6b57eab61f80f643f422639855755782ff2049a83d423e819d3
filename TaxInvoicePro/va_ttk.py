# -*- coding: utf-8 -*-
"""
va_ttk.py - Lop va tuong thich ttk cho Python 3.12 / 3.13 / 3.14
Tu dong loai bo tham so command=None khi dat tieu de cot Treeview,
tranh loi: _tkinter.TclError: value for "-command" missing
Chi can 'import va_ttk' mot lan tai tep khoi dong (app.py).
Tac gia: TDA - 0986509106
"""
from tkinter import ttk as _ttk

if not getattr(_ttk.Treeview, "_va_tda", False):

    _heading_goc = _ttk.Treeview.heading

    def _heading_an_toan(self, column, option=None, **kw):
        if "command" in kw and kw["command"] is None:
            kw.pop("command")
        return _heading_goc(self, column, option, **kw)

    _ttk.Treeview.heading = _heading_an_toan

    _column_goc = _ttk.Treeview.column

    def _column_an_toan(self, column, option=None, **kw):
        for khoa in list(kw):
            if kw[khoa] is None:
                kw.pop(khoa)
        return _column_goc(self, column, option, **kw)

    _ttk.Treeview.column = _column_an_toan

    _ttk.Treeview._va_tda = True
