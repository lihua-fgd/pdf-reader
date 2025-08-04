# -*- coding: utf-8 -*-
"""
超简 PDF 漫画阅读器
- 手机目录：/sdcard/MyPDFs
- 漫画按文件夹分
- PDF 文件名：第xx话.pdf
"""

from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.properties import ListProperty, StringProperty
import re
from pathlib import Path

# 手机里的根目录，可改
ROOT = Path("/sdcard/MyPDFs")


class MangaListScreen(Screen):
    mangas = ListProperty()

    def on_pre_enter(self):
        # 1. 递归扫描所有 pdf
        files = list(ROOT.rglob("*.pdf"))
        pattern = re.compile(r'第?\s*(\d+(?:\.\d+)?)\s*[话卷章]', re.I)

        buckets = {}
        for f in files:
            # 2. 漫画名 = 上一层文件夹的名字
            manga_name = f.parent.name.strip()
            # 3. 章节号从文件名里提数字
            m = pattern.search(f.stem)
            chap = float(m.group(1)) if m else 0
            buckets.setdefault(manga_name, []).append((chap, str(f)))

        # 4. 排序：漫画按字母序，章节按数字序
        self.mangas = sorted(
            [(name, sorted(chaps, key=lambda x: x[0])) for name, chaps in buckets.items()],
            key=lambda x: x[0]
        )


class ChapListScreen(Screen):
    chapters = ListProperty()
    manga_name = StringProperty()


class PdfReaderApp(App):
    def build(self):
        from kivy.lang import Builder
        # 把 kv 语言直接写进字符串，省得再建 kv 文件
        Builder.load_string('''
#:import Path pathlib.Path

<MangaListScreen>:
    BoxLayout:
        orientation: 'vertical'
        RecycleView:
            viewclass: 'OneLineListItem'
            data: [{'text': name} for name, _ in root.mangas]
            RecycleBoxLayout:
                default_size: None, dp(48)
                default_size_hint: 1, None
                size_hint_y: None
                height: self.minimum_height
                orientation: 'vertical'
        Label:
            size_hint_y: None
            height: dp(20)
            text: f'共 {len(root.mangas)} 部'

<OneLineListItem@OneLineAvatarIconListItem>:
    on_release:
        app.root.get_screen('chaps').manga_name = self.text
        app.root.get_screen('chaps').chapters = [c for _, c in next(v for n, v in app.root.get_screen('mangas').mangas if n == self.text)]
        app.root.current = 'chaps'

<ChapListScreen>:
    BoxLayout:
        orientation: 'vertical'
        MDToolbar:
            title: root.manga_name
            left_action_items: [['arrow-left', lambda x: setattr(app.root, 'current', 'mangas')]]
        RecycleView:
            viewclass: 'OneLineListItem'
            data: [{'text': Path(c).stem} for c in root.chapters]
            RecycleBoxLayout:
                default_size: None, dp(48)
                default_size_hint: 1, None
                size_hint_y: None
                height: self.minimum_height
                orientation: 'vertical'

<OneLineListItem>:
    on_release:
        import subprocess, os
        subprocess.call(['am', 'start', '--user', 'current', '-a', 'android.intent.action.VIEW', '-d', 'file://' + self.text, '-t', 'application/pdf'])
        ''')
        sm = ScreenManager()
        sm.add_widget(MangaListScreen(name='mangas'))
        sm.add_widget(ChapListScreen(name='chaps'))
        return sm


if __name__ == '__main__':
    PdfReaderApp().run()