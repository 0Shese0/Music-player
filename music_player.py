import sys
import os
import json
import time
import webbrowser
from datetime import datetime, timedelta
from pathlib import Path
from urllib.parse import quote_plus

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QSlider, QScrollArea, QMenu, QFileDialog,
    QMessageBox, QFrame, QLineEdit, QDialog, QFormLayout, QColorDialog,
    QInputDialog, QStyle, QStyleOptionSlider, QTextEdit, QTextBrowser,
    QGroupBox, QButtonGroup, QDateEdit,
)
from PySide6.QtCore import Qt, QTimer, QUrl, QPoint, Signal, QDate, QRect
from PySide6.QtGui import (
    QPixmap, QPainter, QPainterPath, QColor, QFont,
    QLinearGradient, QBrush, QCursor,
)
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput

try:
    from mutagen import File as MutagenFile
    HAS_MUTAGEN = True
except ImportError:
    HAS_MUTAGEN = False


# ==================================================================
#  НАСТРОЙКИ
# ==================================================================

CONFIG_DIR   = Path.home() / ".music_player"
CONFIG_FILE  = CONFIG_DIR / "config.json"
HISTORY_FILE = CONFIG_DIR / "history.json"
LOG_FILE     = CONFIG_DIR / "player.log"

THEMES = {
    "dark": {
        "name":         "🌙 Тёмная",
        "accent":       "#7c5cff", "accent_hover": "#9d7fff",
        "panel_rgb":    (22, 22, 28), "panel_alpha": 195,
        "text":         "#f0f0f5", "text_dim": "#8a8a95",
        "row_current":  "rgba(124, 92, 255, 70)",
        "row_hover":    "rgba(255, 255, 255, 25)",
        "surface":      "rgba(255, 255, 255, 18)",
        "lyrics_text":  "#e8e8f0",
        "lyrics_bg":    "#0e0e12",
        "search_text":  "#f0f0f5",
        "search_bg":    "#1a1a22",
        "liked_bg":     "#7c5cff",
        "stats_text":   "#8a8a95",
    },
    "light": {
        "name":         "☀️ Светлая",
        "accent":       "#5b47d6", "accent_hover": "#7c6bf0",
        "panel_rgb":    (255, 255, 255), "panel_alpha": 200,
        "text":         "#1a1a20", "text_dim": "#6a6a75",
        "row_current":  "rgba(91, 71, 214, 55)",
        "row_hover":    "rgba(0, 0, 0, 20)",
        "surface":      "rgba(0, 0, 0, 15)",
        "lyrics_text":  "#1a1a20",
        "lyrics_bg":    "#ffffff",
        "search_text":  "#1a1a20",
        "search_bg":    "#f2f2f7",
        "liked_bg":     "#5b47d6",
        "stats_text":   "#6a6a75",
    },
    "blue": {
        "name":         "🌊 Синяя",
        "accent":       "#3f88c5", "accent_hover": "#5ba0dd",
        "panel_rgb":    (14, 30, 48), "panel_alpha": 195,
        "text":         "#e0eaf5", "text_dim": "#7a90a8",
        "row_current":  "rgba(63, 136, 197, 75)",
        "row_hover":    "rgba(255, 255, 255, 22)",
        "surface":      "rgba(255, 255, 255, 18)",
        "lyrics_text":  "#dceaf5",
        "lyrics_bg":    "#081420",
        "search_text":  "#dceaf5",
        "search_bg":    "#0e2236",
        "liked_bg":     "#3f88c5",
        "stats_text":   "#7a90a8",
    },
    "green": {
        "name":         "🌿 Зелёная",
        "accent":       "#4caf50", "accent_hover": "#66bb6a",
        "panel_rgb":    (16, 32, 18), "panel_alpha": 195,
        "text":         "#e0f0e0", "text_dim": "#7a9a7a",
        "row_current":  "rgba(76, 175, 80, 75)",
        "row_hover":    "rgba(255, 255, 255, 22)",
        "surface":      "rgba(255, 255, 255, 18)",
        "lyrics_text":  "#e0f0e0",
        "lyrics_bg":    "#0a180c",
        "search_text":  "#e0f0e0",
        "search_bg":    "#142614",
        "liked_bg":     "#4caf50",
        "stats_text":   "#7a9a7a",
    },
}

DEFAULT_THEME     = "dark"
DEFAULT_LIKED     = "❤ Понравившиеся"
DEFAULT_PLAYLIST  = "Мой плейлист"
BG_DARKEN         = 0.45
COVER_SIZE        = 150
COVER_RADIUS      = 16
CONTENT_MAX_WIDTH = 1000
VOLUME_MAX_WIDTH  = 180
HISTORY_LIMIT     = 50000

G_PLAY        = "▶"
G_PAUSE       = "❚❚"
G_STOP        = "■"
G_PREV        = "◀◀"
G_NEXT        = "▶▶"
G_HEART       = "♥"
G_HEART_EMPTY = "♡"

FAQ_HTML = """
<h2>❓ Часто задаваемые вопросы</h2>

<h3>🎵 Как добавить музыку?</h3>
<p>Кнопки <b>＋ Файлы</b> и <b>📁 Папка</b> внизу приложения.
«Папка» добавляет все аудиофайлы рекурсивно (mp3, wav, ogg, flac, m4a).</p>

<h3>✎ Как изменить название или исполнителя?</h3>
<p>ПКМ по треку → «Информация о треке». Новое имя используется в поиске
и при формировании запроса к Genius.</p>

<h3>🖼 Как сменить обложку?</h3>
<p>Клик по большой обложке в карточке «Now Playing» — откроется меню.
Или ПКМ по треку → «Сменить обложку».</p>

<h3>🌄 Как изменить фон окна?</h3>
<p>Настройки (⚙) → секция «Фон окна» → «Изменить фон».
Можно выбрать любое изображение. Оно автоматически затемняется для читаемости.</p>

<h3>🎨 Как настроить цвета?</h3>
<p>Настройки (⚙) — там секции: «Основные цвета», «Поисковая строка»,
«Понравившиеся и счётчик», «Текст песни», «Фон окна».
Настройки сохраняются отдельно для каждой темы.</p>

<h3>● Что означает кружок в правом верхнем углу?</h3>
<p>Интернет-режим. <b>●</b> — включён, в меню трека доступен пункт «Найти на Genius».
<b>○</b> — выключен, пункт скрыт. Плеер работает офлайн в любом случае.</p>

<h3>📊 Как работают Отчёты?</h3>
<p>Кнопка <b>📊 Отчёты</b> в шапке. Трек засчитывается как прослушанный,
если вы прослушали хотя бы 30% (но не менее 5 и не более 30 секунд).
История хранится в <code>history.json</code> и обрезается до 50 000 записей.
Показываются топ-треки, топ-исполнители, время прослушивания и столбчатая
активность по часам/дням.</p>

<h3>🎤 Как найти текст песни?</h3>
<p>ПКМ по треку → «Найти на Genius» откроет браузер. Скопированный текст вставьте
в <b>📄 Текст</b> (или кнопка в карточке Now Playing). Сохраняется автоматически.
Повторный клик по «📄 Текст» закрывает панель.</p>

<h3>❤ Понравившиеся</h3>
<p>Закреплённый плейлист. Нельзя удалить или переименовать. Чтобы добавить трек —
кликните <b>♡</b> справа или ПКМ → «В понравившиеся».</p>

<h3>💾 Где хранятся настройки?</h3>
<p><code>%USERPROFILE%\\.music_player\\config.json</code> — плейлисты, тема, цвета,
обложки, тексты. <code>history.json</code> — статистика прослушивания.
Удалите файлы для полного сброса.</p>

<h3>⏱ Что показывает счётчик рядом с плейлистом?</h3>
<p>Количество треков и общую длительность. Первый раз может показывать
«считаю длительность…» — значения кешируются в памяти на сеанс.</p>

<h3>⚠ История не пополняется?</h3>
<p>Откройте <code>player.log</code> — там строки <code>commit OK</code>
или <code>commit skip (too short / no duration)</code> с указанием причины.
Если стоит «too short» — вы прослушали меньше порога (5–30 секунд).</p>
"""


# ==================================================================
#  Служебные виджеты
# ==================================================================

class ClickableSlider(QSlider):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setMinimumHeight(26)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            opt = QStyleOptionSlider()
            self.initStyleOption(opt)
            handle = self.style().subControlRect(
                QStyle.CC_Slider, opt, QStyle.SC_SliderHandle, self)
            if not handle.contains(event.position().toPoint()):
                val = QStyle.sliderValueFromPosition(
                    self.minimum(), self.maximum(),
                    int(event.position().x()), self.width(), opt.upsideDown)
                self.setValue(val)
                self.sliderMoved.emit(val)
        super().mousePressEvent(event)


class ClickableLabel(QLabel):
    clicked = Signal()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)


# ==================================================================
#  Виджеты диаграмм
# ==================================================================

class PieChartWidget(QWidget):
    def __init__(self, title, text_color, palette, parent=None):
        super().__init__(parent)
        self.title = title
        self.text_color = text_color
        self.palette = palette
        self.entries = []
        self.setMinimumHeight(320)

    def set_data(self, entries):
        self.entries = entries
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()

        p.setPen(QColor(self.text_color))
        f = QFont("Segoe UI", 11); f.setBold(True); p.setFont(f)
        p.drawText(QRect(0, 5, w, 22), Qt.AlignHCenter | Qt.AlignTop, self.title)

        if not self.entries or sum(v for _, v in self.entries) <= 0:
            p.setFont(QFont("Segoe UI", 10))
            p.drawText(self.rect(), Qt.AlignCenter, "Нет данных за период")
            return

        pie_size = min(w - 40, h - 180)
        if pie_size < 80:
            return
        pie_rect = QRect((w - pie_size) // 2, 32, pie_size, pie_size)

        total = sum(v for _, v in self.entries)
        start_angle = 90 * 16
        for i, (_, value) in enumerate(self.entries):
            span = int(value / total * 360 * 16)
            p.setBrush(QColor(self.palette[i % len(self.palette)]))
            p.setPen(Qt.NoPen)
            p.drawPie(pie_rect, start_angle, -span)
            start_angle -= span

        y = pie_rect.bottom() + 12
        p.setFont(QFont("Segoe UI", 9))
        for i, (label, value) in enumerate(self.entries):
            if y + 18 > h:
                break
            color = QColor(self.palette[i % len(self.palette)])
            p.setBrush(color); p.setPen(Qt.NoPen)
            p.drawRoundedRect(10, y + 3, 12, 12, 3, 3)

            p.setPen(QColor(self.text_color))
            pct = value / total * 100
            text = f"{label} — {value} ({pct:.0f}%)"
            metrics = p.fontMetrics()
            text = metrics.elidedText(text, Qt.ElideRight, w - 40)
            p.drawText(28, y, w - 36, 18, Qt.AlignLeft | Qt.AlignVCenter, text)
            y += 20


class BarChartWidget(QWidget):
    def __init__(self, title, text_color, accent_color, parent=None):
        super().__init__(parent)
        self.title = title
        self.text_color = text_color
        self.accent_color = accent_color
        self.values = []
        self.labels = []
        self.highlight = -1
        self.setMinimumHeight(150)

    def set_data(self, values, labels, highlight=-1):
        self.values = values
        self.labels = labels
        self.highlight = highlight
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()

        p.setPen(QColor(self.text_color))
        f = QFont("Segoe UI", 10); f.setBold(True); p.setFont(f)
        p.drawText(QRect(0, 2, w, 18), Qt.AlignHCenter | Qt.AlignTop, self.title)

        if not self.values or max(self.values) <= 0:
            p.setFont(QFont("Segoe UI", 9))
            p.drawText(self.rect(), Qt.AlignCenter, "Нет данных")
            return

        chart_top = 26
        chart_bottom = h - 22
        chart_h = chart_bottom - chart_top
        if chart_h < 20:
            return

        n = len(self.values)
        max_val = max(self.values)
        slot = (w - 40) / n
        bar_w = max(3, int(slot * 0.7))

        p.setFont(QFont("Segoe UI", 7))
        for i, (val, label) in enumerate(zip(self.values, self.labels)):
            x = int(20 + i * slot + slot / 2 - bar_w / 2)
            bh = int((val / max_val) * chart_h) if max_val > 0 else 0

            color = QColor(self.accent_color)
            if i == self.highlight:
                color = color.lighter(125)
            else:
                color.setAlpha(190)
            p.setBrush(color)
            p.setPen(Qt.NoPen)

            if bh > 2:
                p.drawRoundedRect(x, chart_bottom - bh, bar_w, bh, 3, 3)
            else:
                p.setBrush(QColor(self.text_color))
                p.drawRoundedRect(x, chart_bottom - 1, bar_w, 2, 1, 1)

            p.setPen(QColor(self.text_color))
            p.drawText(x - 6, chart_bottom + 2, bar_w + 12, 16,
                       Qt.AlignHCenter | Qt.AlignTop, label)


# ==================================================================
#  Диалоги
# ==================================================================

class TrackInfoDialog(QDialog):
    def __init__(self, parent, name, artist):
        super().__init__(parent)
        self.setWindowTitle("Информация о треке")
        self.setStyleSheet(parent.styleSheet())
        self.setMinimumWidth(380)

        form = QFormLayout(self)

        self.name_edit = QLineEdit(name)
        self.name_edit.setPlaceholderText("Отображаемое название")
        form.addRow("Название:", self.name_edit)

        self.artist_edit = QLineEdit(artist)
        self.artist_edit.setPlaceholderText("Исполнитель")
        form.addRow("Исполнитель:", self.artist_edit)

        btns = QHBoxLayout()
        cancel = QPushButton("Отмена"); cancel.clicked.connect(self.reject)
        ok = QPushButton("Сохранить"); ok.clicked.connect(self.accept)
        ok.setDefault(True)
        btns.addStretch(); btns.addWidget(cancel); btns.addWidget(ok)
        form.addRow(btns)

    def values(self):
        return self.name_edit.text().strip(), self.artist_edit.text().strip()


class FAQDialog(QDialog):
    def __init__(self, parent, player):
        super().__init__(parent)
        self.setWindowTitle("FAQ — частые вопросы")
        self.setStyleSheet(player.styleSheet())
        self.resize(680, 620)

        t = player.theme()
        r, g, b = t["panel_rgb"]

        layout = QVBoxLayout(self)
        browser = QTextBrowser()
        browser.setHtml(FAQ_HTML)
        browser.setOpenExternalLinks(True)
        browser.setStyleSheet(
            f"QTextBrowser {{"
            f"  background: rgba({r},{g},{b},230);"
            f"  color: {t['text']};"
            f"  border: 1px solid rgba(255,255,255,20);"
            f"  border-radius: 12px;"
            f"  padding: 12px;"
            f"}}"
        )
        layout.addWidget(browser)

        ok_btn = QPushButton("Понятно")
        ok_btn.clicked.connect(self.accept)
        ok_btn.setDefault(True)
        layout.addWidget(ok_btn)


class ReportsDialog(QDialog):
    def __init__(self, player):
        super().__init__(player)
        self.player = player
        self.mode = "week"
        self.setWindowTitle("📊  Отчёты")
        self.setStyleSheet(player.styleSheet())
        self.resize(920, 820)
        self.setMinimumSize(760, 680)

        t = player.theme()
        self.text_color = t["text"]
        self.accent_color = t["accent"]
        self.palette = self._make_palette()

        main = QVBoxLayout(self)
        main.setContentsMargins(16, 16, 16, 16)
        main.setSpacing(12)

        top = QHBoxLayout()
        top.setSpacing(8)

        self.mode_group = QButtonGroup(self)
        self.mode_group.setExclusive(True)
        self.mode_btns = {}
        for key, label in (("day", "День"), ("week", "Неделя"), ("month", "Месяц")):
            b = QPushButton(label)
            b.setCheckable(True)
            b.setObjectName("segment")
            b.clicked.connect(lambda checked, k=key: self._on_mode_click(k))
            self.mode_group.addButton(b)
            self.mode_btns[key] = b
            top.addWidget(b)
        self.mode_btns["week"].setChecked(True)

        top.addSpacing(16)
        top.addWidget(QLabel("Дата:"))
        self.date_edit = QDateEdit()
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setDate(QDate.currentDate())
        self.date_edit.setDisplayFormat("dd.MM.yyyy")
        self.date_edit.dateChanged.connect(self._refresh)
        top.addWidget(self.date_edit)

        today_btn = QPushButton("Сегодня")
        today_btn.clicked.connect(lambda: self.date_edit.setDate(QDate.currentDate()))
        top.addWidget(today_btn)

        top.addStretch()
        main.addLayout(top)

        cards = QHBoxLayout()
        cards.setSpacing(10)
        self.card_time = self._make_card("Время прослушивания")
        self.card_count = self._make_card("Треков прослушано")
        self.card_artists = self._make_card("Уникальных исполнителей")
        self.card_compare = self._make_card("Сравнение с прошлым")
        for c in (self.card_time, self.card_count, self.card_artists, self.card_compare):
            cards.addWidget(c)
        main.addLayout(cards)

        pies = QHBoxLayout()
        pies.setSpacing(10)
        self.pie_tracks = PieChartWidget("Топ треков", self.text_color, self.palette)
        self.pie_artists = PieChartWidget("Топ исполнителей", self.text_color, self.palette)
        pies.addWidget(self.pie_tracks, 1)
        pies.addWidget(self.pie_artists, 1)
        main.addLayout(pies, 1)

        self.bar_chart = BarChartWidget("Активность", self.text_color, self.accent_color)
        self.bar_chart.setMinimumHeight(160)
        main.addWidget(self.bar_chart)

        close = QPushButton("Закрыть")
        close.clicked.connect(self.accept)
        main.addWidget(close, 0, Qt.AlignRight)

        self._refresh()

    def _make_palette(self):
        accent = QColor(self.accent_color)
        base_hue = accent.hue()
        base_sat = max(150, accent.saturation())
        palette = []
        for i in range(7):
            h = (base_hue + i * 45) % 360
            v = 225 if i % 2 == 0 else 180
            palette.append(QColor.fromHsv(h, base_sat, v).name())
        return palette

    def _make_card(self, title):
        t = self.player.theme()
        card = QFrame()
        card.setObjectName("glassPanel")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(14, 10, 14, 10)

        title_lbl = QLabel(title)
        title_lbl.setStyleSheet(f"color: {t['text_dim']}; font-size: 11px;")
        value_lbl = QLabel("—")
        f = value_lbl.font(); f.setPointSize(15); f.setBold(True)
        value_lbl.setFont(f)
        value_lbl.setStyleSheet(f"color: {t['text']};")

        layout.addWidget(title_lbl)
        layout.addWidget(value_lbl)
        card._value_lbl = value_lbl
        return card

    def _on_mode_click(self, key):
        self.mode = key
        self._refresh()

    def _get_period(self):
        qd = self.date_edit.date()
        # PySide6: QDate.toPyDate() нет — собираем datetime вручную
        d = datetime(qd.year(), qd.month(), qd.day())
        if self.mode == "day":
            start = d
            end = start + timedelta(days=1)
        elif self.mode == "week":
            monday = d - timedelta(days=d.weekday())
            start = monday
            end = start + timedelta(days=7)
        else:
            start = datetime(d.year, d.month, 1)
            end = (datetime(d.year + 1, 1, 1) if d.month == 12
                   else datetime(d.year, d.month + 1, 1))
        return start.timestamp(), end.timestamp()

    def _aggregate(self, start_ts, end_ts):
        counts = {}
        artists = {}
        total_dur = 0.0
        total_count = 0
        for e in self.player.history:
            ts = e.get("ts", 0)
            if start_ts <= ts < end_ts:
                path = e["path"]
                counts[path] = counts.get(path, 0) + 1
                artist = self.player._display_artist(path) or "Неизвестный"
                artists[artist] = artists.get(artist, 0) + 1
                total_dur += e.get("dur", 0)
                total_count += 1
        return counts, artists, total_dur, total_count

    def _refresh(self):
        start_ts, end_ts = self._get_period()
        counts, artists, total_dur, total_count = self._aggregate(start_ts, end_ts)

        self.card_time._value_lbl.setText(self._fmt_duration(total_dur))
        self.card_count._value_lbl.setText(str(total_count))
        self.card_artists._value_lbl.setText(str(len(artists)))

        prev_start = start_ts - (end_ts - start_ts)
        prev_end = start_ts
        _, _, prev_dur, _ = self._aggregate(prev_start, prev_end)
        if prev_dur > 0:
            delta = (total_dur - prev_dur) / prev_dur * 100
            sign = "+" if delta >= 0 else ""
            self.card_compare._value_lbl.setText(f"{sign}{delta:.0f}%")
        else:
            self.card_compare._value_lbl.setText("—")

        top_tracks = self._top_n(counts, 5)
        top_artists = self._top_n(artists, 5)

        named_tracks = []
        for key, cnt in top_tracks:
            if key == "Другие":
                named_tracks.append((key, cnt))
            else:
                named_tracks.append((self.player._display_name(key), cnt))

        self.pie_tracks.set_data(named_tracks)
        self.pie_artists.set_data(top_artists)
        self._update_bar_chart(start_ts, end_ts)

    def _top_n(self, items, n=5):
        sorted_items = sorted(items.items(), key=lambda x: -x[1])
        if len(sorted_items) <= n:
            return sorted_items
        top = sorted_items[:n]
        rest = sum(v for _, v in sorted_items[n:])
        top.append(("Другие", rest))
        return top

    def _update_bar_chart(self, start_ts, end_ts):
        if self.mode == "day":
            values = [0] * 24
            labels = [f"{h:02d}" for h in range(24)]
            for e in self.player.history:
                ts = e.get("ts", 0)
                if start_ts <= ts < end_ts:
                    values[datetime.fromtimestamp(ts).hour] += 1
        elif self.mode == "week":
            values = [0] * 7
            labels = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]
            for e in self.player.history:
                ts = e.get("ts", 0)
                if start_ts <= ts < end_ts:
                    values[datetime.fromtimestamp(ts).weekday()] += 1
        else:
            start_date = datetime.fromtimestamp(start_ts).date()
            next_month = (datetime(start_date.year + 1, 1, 1).date()
                          if start_date.month == 12
                          else datetime(start_date.year, start_date.month + 1, 1).date())
            days = (next_month - start_date).days
            values = [0] * days
            labels = [str(i + 1) for i in range(days)]
            for e in self.player.history:
                ts = e.get("ts", 0)
                if start_ts <= ts < end_ts:
                    d = datetime.fromtimestamp(ts).date()
                    idx = (d - start_date).days
                    if 0 <= idx < days:
                        values[idx] += 1

        highlight = -1
        if values and max(values) > 0:
            highlight = values.index(max(values))
        self.bar_chart.set_data(values, labels, highlight)

    @staticmethod
    def _fmt_duration(seconds):
        if seconds <= 0:
            return "0 мин"
        s = int(seconds)
        h, rem = divmod(s, 3600)
        m = rem // 60
        if h > 0:
            return f"{h} ч {m} мин"
        if m > 0:
            return f"{m} мин"
        return f"{s} сек"


class ColorSettingsDialog(QDialog):
    def __init__(self, player):
        super().__init__(player)
        self.player = player
        self.setWindowTitle("⚙  Настройки")
        self.setStyleSheet(player.styleSheet())
        self.resize(580, 0)
        self.setMinimumWidth(560)

        base     = THEMES[player._theme_name]
        override = player.theme_overrides.get(player._theme_name, {})

        self.accent      = QColor(override.get("accent",      base["accent"]))
        self.panel_rgb   = QColor(*override.get("panel_rgb",  base["panel_rgb"]))
        self.panel_alpha = int(override.get("panel_alpha",    base["panel_alpha"]))
        self.lyrics_text = QColor(override.get("lyrics_text", base["lyrics_text"]))
        self.lyrics_bg   = QColor(override.get("lyrics_bg",   base["lyrics_bg"]))
        self.search_text = QColor(override.get("search_text", base["search_text"]))
        self.search_bg   = QColor(override.get("search_bg",   base["search_bg"]))
        self.liked_bg    = QColor(override.get("liked_bg",    base["liked_bg"]))
        self.stats_text  = QColor(override.get("stats_text",  base["stats_text"]))

        main = QVBoxLayout(self)
        main.setSpacing(10)
        main.setContentsMargins(14, 14, 14, 14)

        gb_basic = QGroupBox("🎨  Основные цвета")
        fb = QFormLayout(gb_basic)
        fb.setContentsMargins(14, 22, 14, 12)
        fb.setSpacing(8)

        self.accent_btn = QPushButton()
        self.accent_btn.clicked.connect(self._pick_accent)
        self._update_color_btn(self.accent_btn, self.accent)
        fb.addRow("Акцентный цвет:", self.accent_btn)

        self.panel_btn = QPushButton()
        self.panel_btn.clicked.connect(self._pick_panel)
        self._update_color_btn(self.panel_btn, self.panel_rgb)
        fb.addRow("Цвет панелей:", self.panel_btn)

        alpha_row = QHBoxLayout()
        self.alpha_slider = QSlider(Qt.Horizontal)
        self.alpha_slider.setRange(0, 255)
        self.alpha_slider.setValue(self.panel_alpha)
        self.alpha_label = QLabel(str(self.panel_alpha))
        self.alpha_label.setMinimumWidth(34)
        self.alpha_slider.valueChanged.connect(
            lambda v: self.alpha_label.setText(str(v)))
        alpha_row.addWidget(self.alpha_slider, 1)
        alpha_row.addWidget(self.alpha_label)
        fb.addRow("Прозрачность (0–255):", alpha_row)
        main.addWidget(gb_basic)

        gb_search = QGroupBox("🔍  Поисковая строка")
        fs = QFormLayout(gb_search)
        fs.setContentsMargins(14, 22, 14, 12)
        fs.setSpacing(8)
        self.search_text_btn = QPushButton()
        self.search_text_btn.clicked.connect(self._pick_search_text)
        self._update_color_btn(self.search_text_btn, self.search_text)
        fs.addRow("Цвет текста:", self.search_text_btn)
        self.search_bg_btn = QPushButton()
        self.search_bg_btn.clicked.connect(self._pick_search_bg)
        self._update_color_btn(self.search_bg_btn, self.search_bg)
        fs.addRow("Фон строки:", self.search_bg_btn)
        main.addWidget(gb_search)

        gb_liked = QGroupBox("⭐  Понравившиеся и счётчик")
        flk = QFormLayout(gb_liked)
        flk.setContentsMargins(14, 22, 14, 12)
        flk.setSpacing(8)
        self.liked_bg_btn = QPushButton()
        self.liked_bg_btn.clicked.connect(self._pick_liked_bg)
        self._update_color_btn(self.liked_bg_btn, self.liked_bg)
        flk.addRow("Фон кнопки «Понравившиеся»:", self.liked_bg_btn)
        self.stats_text_btn = QPushButton()
        self.stats_text_btn.clicked.connect(self._pick_stats_text)
        self._update_color_btn(self.stats_text_btn, self.stats_text)
        flk.addRow("Текст счётчика (треки · время):", self.stats_text_btn)
        main.addWidget(gb_liked)

        gb_lyrics = QGroupBox("📄  Текст песни")
        fl = QFormLayout(gb_lyrics)
        fl.setContentsMargins(14, 22, 14, 12)
        fl.setSpacing(8)
        self.lyrics_text_btn = QPushButton()
        self.lyrics_text_btn.clicked.connect(self._pick_lyrics_text)
        self._update_color_btn(self.lyrics_text_btn, self.lyrics_text)
        fl.addRow("Цвет текста:", self.lyrics_text_btn)
        self.lyrics_bg_btn = QPushButton()
        self.lyrics_bg_btn.clicked.connect(self._pick_lyrics_bg)
        self._update_color_btn(self.lyrics_bg_btn, self.lyrics_bg)
        fl.addRow("Фон панели:", self.lyrics_bg_btn)
        main.addWidget(gb_lyrics)

        gb_bg = QGroupBox("🖼  Фон окна")
        fbg = QHBoxLayout(gb_bg)
        fbg.setContentsMargins(14, 22, 14, 12)
        fbg.setSpacing(8)
        bg_btn = QPushButton("🖼  Изменить фон")
        bg_btn.clicked.connect(self._change_bg)
        fbg.addWidget(bg_btn)
        self.remove_bg_btn = QPushButton("✕  Убрать фон")
        self.remove_bg_btn.clicked.connect(self._remove_bg)
        self.remove_bg_btn.setEnabled(bool(player.background_path))
        fbg.addWidget(self.remove_bg_btn)
        fbg.addStretch()
        main.addWidget(gb_bg)

        faq_row = QHBoxLayout()
        faq_btn = QPushButton("❓  FAQ — частые вопросы")
        faq_btn.clicked.connect(self._open_faq)
        faq_row.addWidget(faq_btn)
        faq_row.addStretch()
        main.addLayout(faq_row)

        btns = QHBoxLayout()
        reset = QPushButton("Сбросить к теме"); reset.clicked.connect(self._reset)
        cancel = QPushButton("Отмена"); cancel.clicked.connect(self.reject)
        apply_btn = QPushButton("Применить"); apply_btn.clicked.connect(self._apply)
        apply_btn.setDefault(True)
        btns.addWidget(reset); btns.addStretch()
        btns.addWidget(cancel); btns.addWidget(apply_btn)
        main.addLayout(btns)

        self.adjustSize()

    @staticmethod
    def _update_color_btn(btn, color):
        lum = (color.red() * 299 + color.green() * 587 + color.blue() * 114) / 1000
        fg = "#000000" if lum > 140 else "#ffffff"
        btn.setText(color.name().upper())
        btn.setStyleSheet(
            f"background-color: {color.name()}; color: {fg}; "
            f"font-weight: bold; padding: 6px 12px; border-radius: 8px;")

    def _pick_accent(self):
        c = QColorDialog.getColor(self.accent, self, "Акцентный цвет")
        if c.isValid():
            self.accent = c; self._update_color_btn(self.accent_btn, self.accent)

    def _pick_panel(self):
        c = QColorDialog.getColor(self.panel_rgb, self, "Цвет панелей")
        if c.isValid():
            self.panel_rgb = c; self._update_color_btn(self.panel_btn, self.panel_rgb)

    def _pick_search_text(self):
        c = QColorDialog.getColor(self.search_text, self, "Цвет текста поиска")
        if c.isValid():
            self.search_text = c; self._update_color_btn(self.search_text_btn, self.search_text)

    def _pick_search_bg(self):
        c = QColorDialog.getColor(self.search_bg, self, "Фон поисковой строки")
        if c.isValid():
            self.search_bg = c; self._update_color_btn(self.search_bg_btn, self.search_bg)

    def _pick_liked_bg(self):
        c = QColorDialog.getColor(self.liked_bg, self, "Фон Понравившиеся")
        if c.isValid():
            self.liked_bg = c; self._update_color_btn(self.liked_bg_btn, self.liked_bg)

    def _pick_stats_text(self):
        c = QColorDialog.getColor(self.stats_text, self, "Цвет счётчика")
        if c.isValid():
            self.stats_text = c; self._update_color_btn(self.stats_text_btn, self.stats_text)

    def _pick_lyrics_text(self):
        c = QColorDialog.getColor(self.lyrics_text, self, "Цвет текста песни")
        if c.isValid():
            self.lyrics_text = c; self._update_color_btn(self.lyrics_text_btn, self.lyrics_text)

    def _pick_lyrics_bg(self):
        c = QColorDialog.getColor(self.lyrics_bg, self, "Фон панели текста")
        if c.isValid():
            self.lyrics_bg = c; self._update_color_btn(self.lyrics_bg_btn, self.lyrics_bg)

    def _change_bg(self):
        self.player._set_background()
        self.remove_bg_btn.setEnabled(bool(self.player.background_path))

    def _remove_bg(self):
        self.player._clear_background()
        self.remove_bg_btn.setEnabled(False)

    def _open_faq(self):
        FAQDialog(self, self.player).exec()

    def _reset(self):
        self.player.theme_overrides.pop(self.player._theme_name, None)
        self.player.apply_theme()
        self.player.save_config()
        self.accept()

    def _apply(self):
        self.player.theme_overrides[self.player._theme_name] = {
            "accent":       self.accent.name(),
            "panel_rgb":    [self.panel_rgb.red(), self.panel_rgb.green(),
                             self.panel_rgb.blue()],
            "panel_alpha":  int(self.alpha_slider.value()),
            "lyrics_text":  self.lyrics_text.name(),
            "lyrics_bg":    self.lyrics_bg.name(),
            "search_text":  self.search_text.name(),
            "search_bg":    self.search_bg.name(),
            "liked_bg":     self.liked_bg.name(),
            "stats_text":   self.stats_text.name(),
        }
        self.player.apply_theme()
        self.player.save_config()
        self.accept()


# ==================================================================
#  CentralWidget
# ==================================================================

class CentralWidget(QWidget):
    def __init__(self, player):
        super().__init__()
        self.player = player
        self._bg_pixmap = None

    def set_background(self, path):
        if path and os.path.isfile(path):
            pix = QPixmap(path)
            if not pix.isNull():
                self._bg_pixmap = pix
                self.update()
                return
        self._bg_pixmap = None
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        if self._bg_pixmap:
            scaled = self._bg_pixmap.scaled(
                self.size(), Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
            x = max(0, (scaled.width() - self.width()) // 2)
            y = max(0, (scaled.height() - self.height()) // 2)
            p.drawPixmap(-x, -y, scaled)
            p.fillRect(self.rect(), QColor(0, 0, 0, int(255 * BG_DARKEN)))
        else:
            rgb = self.player.theme()["panel_rgb"]
            p.fillRect(self.rect(), QColor(rgb[0] // 2, rgb[1] // 2, rgb[2] // 2))
        p.end()


# ==================================================================
#  Основной класс
# ==================================================================

class MusicPlayer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Music Player")
        self.resize(700, 940)
        self.setMinimumSize(560, 760)

        self.player = QMediaPlayer(self)
        self.audio  = QAudioOutput(self)
        self.player.setAudioOutput(self.audio)

        # состояние
        self._theme_name      = DEFAULT_THEME
        self._saved_vol       = 70
        self.internet_enabled = True
        self.playlists        = {DEFAULT_LIKED: [], DEFAULT_PLAYLIST: []}
        self.active_playlist  = DEFAULT_PLAYLIST
        self.playlist         = self.playlists[self.active_playlist]
        self.metadata         = {}
        self.theme_overrides  = {}
        self.background_path  = ""
        self.current_index    = -1
        self._dragging_seek   = False
        self._advancing       = False
        self.track_rows       = []

        # история прослушивания
        self.history = []
        self._playing_path = None
        self._play_started_at = None
        self._current_duration_ms = 0

        self._row_style_cache = {}

        self._filter_timer = QTimer(self)
        self._filter_timer.setSingleShot(True)
        self._filter_timer.setInterval(200)
        self._filter_timer.timeout.connect(self.rebuild_playlist)

        self._duration_cache = {}
        self._duration_gen   = 0
        self._duration_idx   = 0
        self._duration_total = 0.0
        self._duration_base  = ""

        self._volume_save_timer = QTimer(self)
        self._volume_save_timer.setSingleShot(True)
        self._volume_save_timer.setInterval(600)
        self._volume_save_timer.timeout.connect(self.save_config)

        self._lyrics_path       = None
        self._lyrics_save_timer = QTimer(self)
        self._lyrics_save_timer.setSingleShot(True)
        self._lyrics_save_timer.setInterval(500)
        self._lyrics_save_timer.timeout.connect(self._save_lyrics_now)

        self.load_config()
        self.load_history()

        self.central = CentralWidget(self)
        self.setCentralWidget(self.central)
        self.central.set_background(self.background_path)

        self.build_ui()
        self.apply_theme()
        self.rebuild_playlist()
        self.restore_status()

        self.player.positionChanged.connect(self._on_position)
        self.player.durationChanged.connect(self._on_duration)
        self.player.mediaStatusChanged.connect(self._on_media_status)
        self.player.playbackStateChanged.connect(self._on_state)
        self.player.errorOccurred.connect(self._on_error)

        self.audio.setVolume(self._saved_vol / 100)
        self.volume_slider.setValue(self._saved_vol)
        self._update_volume_label(self._saved_vol)
        self._volume_save_timer.stop()

        self._log(f"=== start, history entries: {len(self.history)} ===")

    # ------------------------------------------------------------------
    #  Логи / тема / конфиг
    # ------------------------------------------------------------------
    def _log(self, msg):
        try:
            CONFIG_DIR.mkdir(parents=True, exist_ok=True)
            ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            with open(LOG_FILE, "a", encoding="utf-8") as f:
                f.write(f"[{ts}] {msg}\n")
        except Exception:
            pass

    def theme(self):
        base = dict(THEMES[self._theme_name])
        ov = self.theme_overrides.get(self._theme_name)
        if ov:
            if "accent" in ov:
                base["accent"] = ov["accent"]
                base["accent_hover"] = QColor(ov["accent"]).lighter(135).name()
            for k in ("panel_rgb", "panel_alpha", "lyrics_text", "lyrics_bg",
                      "search_text", "search_bg", "liked_bg", "stats_text"):
                if k in ov:
                    base[k] = ov[k] if k != "panel_rgb" else tuple(ov[k])
        return base

    def load_config(self):
        try:
            if not CONFIG_FILE.exists():
                return
            data = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
            t = data.get("theme", DEFAULT_THEME)
            if t in THEMES:
                self._theme_name = t
            self._saved_vol = max(0, min(100, int(data.get("volume", 70))))
            self.internet_enabled = bool(data.get("internet_enabled", True))

            if "playlists" not in data and "playlist" in data:
                self.playlists = {
                    DEFAULT_LIKED: [],
                    DEFAULT_PLAYLIST: list(data.get("playlist", [])),
                }
            else:
                pl = data.get("playlists", {})
                if isinstance(pl, dict) and pl:
                    self.playlists = {str(k): list(v) for k, v in pl.items()}

            if DEFAULT_LIKED not in self.playlists:
                self.playlists = {DEFAULT_LIKED: []} | self.playlists

            ap = data.get("active_playlist", DEFAULT_PLAYLIST)
            self.active_playlist = ap if ap in self.playlists else DEFAULT_PLAYLIST
            if self.active_playlist not in self.playlists:
                self.active_playlist = next(iter(self.playlists))

            self.playlist = self.playlists[self.active_playlist]
            self.metadata = data.get("metadata", {}) or {}
            self.theme_overrides = data.get("theme_overrides", {}) or {}
            self.background_path = data.get("background", "") or ""
        except Exception as e:
            self._log("load_config: " + repr(e))

    def save_config(self):
        try:
            CONFIG_DIR.mkdir(parents=True, exist_ok=True)
            self.playlists[self.active_playlist] = self.playlist
            data = {
                "theme":            self._theme_name,
                "volume":           int(self.volume_slider.value()),
                "playlists":        self.playlists,
                "active_playlist":  self.active_playlist,
                "metadata":         self.metadata,
                "theme_overrides":  self.theme_overrides,
                "background":       self.background_path,
                "internet_enabled": self.internet_enabled,
            }
            tmp = CONFIG_FILE.with_suffix(".json.tmp")
            tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2),
                           encoding="utf-8")
            os.replace(tmp, CONFIG_FILE)
        except Exception as e:
            self._log("save_config: " + repr(e))

    # ------------------------------------------------------------------
    #  История прослушивания
    # ------------------------------------------------------------------
    def load_history(self):
        try:
            CONFIG_DIR.mkdir(parents=True, exist_ok=True)
            if not HISTORY_FILE.exists():
                HISTORY_FILE.write_text("[]", encoding="utf-8")
                return
            data = json.loads(HISTORY_FILE.read_text(encoding="utf-8"))
            if isinstance(data, list):
                self.history = [e for e in data
                                if isinstance(e, dict) and "path" in e and "ts" in e]
        except Exception as e:
            self._log("load_history: " + repr(e))

    def save_history(self):
        try:
            CONFIG_DIR.mkdir(parents=True, exist_ok=True)
            tmp = HISTORY_FILE.with_suffix(".json.tmp")
            tmp.write_text(json.dumps(self.history, ensure_ascii=False),
                           encoding="utf-8")
            os.replace(tmp, HISTORY_FILE)
        except Exception as e:
            self._log("save_history: " + repr(e))

    def _trim_history(self):
        if len(self.history) > HISTORY_LIMIT:
            self.history = self.history[-HISTORY_LIMIT:]

    def _commit_play(self, force_dur=None):
        path = self._playing_path
        started_at = self._play_started_at
        self._playing_path = None
        self._play_started_at = None
        if not path or started_at is None:
            return

        # длительность: сначала у плеера, если обнулил — из кэша
        dur_ms = self.player.duration()
        if dur_ms <= 0:
            dur_ms = self._current_duration_ms
        dur_sec = dur_ms / 1000.0

        if dur_sec <= 0:
            self._log(f"commit skip (no duration): {path}")
            return

        if force_dur is not None:
            listened = force_dur
        else:
            pos_sec = self.player.position() / 1000.0
            if pos_sec <= 0:
                # плеер обнулил позицию — вероятно, трек дослушан
                pos_sec = dur_sec
            listened = min(pos_sec, dur_sec)

        threshold = min(30.0, max(5.0, dur_sec * 0.3))
        if listened < threshold:
            self._log(f"commit skip (too short): {path} "
                      f"listened={listened:.1f} threshold={threshold:.1f}")
            return

        self.history.append({
            "path": path,
            "ts": started_at,
            "dur": round(listened, 1),
        })
        self._trim_history()
        self.save_history()
        self._log(f"commit OK: {path} listened={listened:.1f} "
                  f"total_entries={len(self.history)}")

    # ------------------------------------------------------------------
    #  QSS
    # ------------------------------------------------------------------
    def build_qss(self):
        t = self.theme()
        r, g, b = t["panel_rgb"]
        a = t["panel_alpha"]
        liked_hover = QColor(t["liked_bg"]).lighter(120).name()
        return f"""
        QMainWindow {{ background: transparent; }}
        QLabel {{ background: transparent; color: {t['text']}; }}
        QLabel#dim {{ color: {t['text_dim']}; font-size: 11px; }}
        QLabel#volval {{ color: {t['text']}; font-size: 11px; font-weight: bold; }}
        QLabel#stats {{ color: {t['stats_text']}; font-size: 11px; }}

        QFrame#glassPanel {{
            background-color: rgba({r},{g},{b},{a});
            border-radius: 22px;
            border: 1px solid rgba(255,255,255,18);
        }}
        QFrame#vsep {{ background-color: rgba(255,255,255,45); border: none; border-radius: 1px; }}

        QPushButton {{
            background-color: {t['accent']};
            color: #ffffff;
            border: none; border-radius: 12px;
            padding: 8px 14px;
            font-size: 12px; font-weight: bold;
        }}
        QPushButton:hover {{ background-color: {t['accent_hover']}; }}
        QPushButton:disabled {{ background-color: {t['surface']}; color: {t['text_dim']}; }}

        QPushButton#secondary {{
            background-color: {t['surface']};
            color: {t['text']}; font-weight: normal;
        }}
        QPushButton#secondary:hover {{ background-color: {t['accent']}; color: white; }}

        QPushButton#icon {{
            background-color: {t['surface']};
            color: {t['text']}; font-size: 13px; padding: 0px;
        }}
        QPushButton#icon:hover {{ background-color: {t['accent']}; color: white; }}

        QPushButton#liked_btn {{
            background-color: {t['liked_bg']};
            color: #ffffff; font-size: 13px; padding: 0px;
            border-radius: 12px; border: none;
        }}
        QPushButton#liked_btn:hover {{ background-color: {liked_hover}; }}

        QPushButton#net {{
            background-color: {t['surface']};
            color: {t['text_dim']}; font-size: 13px; padding: 0px;
            border-radius: 12px; border: none;
        }}
        QPushButton#net[online="true"] {{ color: {t['accent']}; }}
        QPushButton#net:hover {{ background-color: {t['accent']}; color: white; }}

        QPushButton#like {{
            background-color: transparent;
            color: {t['text_dim']}; font-size: 18px; border-radius: 8px; padding: 0px;
        }}
        QPushButton#like:hover {{ background-color: {t['surface']}; }}
        QPushButton#like[liked="true"] {{ color: {t['accent']}; }}

        QPushButton#play {{
            background-color: {t['accent']};
            color: white; font-size: 18px;
            border-radius: 16px; padding: 0px;
        }}
        QPushButton#play:hover {{ background-color: {t['accent_hover']}; }}

        QPushButton#segment {{
            background-color: {t['surface']};
            color: {t['text']}; font-weight: normal;
            border: none; border-radius: 10px;
            padding: 6px 16px;
        }}
        QPushButton#segment:checked {{
            background-color: {t['accent']};
            color: #ffffff; font-weight: bold;
        }}

        QSlider::groove:horizontal {{
            height: 6px; background: rgba(255,255,255,40); border-radius: 3px;
        }}
        QSlider::sub-page:horizontal {{ background: {t['accent']}; border-radius: 3px; }}
        QSlider::handle:horizontal {{
            background: {t['accent']}; width: 16px; height: 16px;
            margin: -5px 0; border-radius: 8px;
        }}
        QSlider::handle:horizontal:hover {{ background: {t['accent_hover']}; }}

        QLineEdit {{
            background-color: {t['search_bg']};
            color: {t['search_text']};
            border: 1px solid rgba(255,255,255,25);
            border-radius: 12px; padding: 8px 12px; font-size: 12px;
            selection-background-color: {t['accent']};
            selection-color: #ffffff;
        }}
        QLineEdit:focus {{ border: 1px solid {t['accent']}; }}

        QDateEdit {{
            background-color: {t['search_bg']};
            color: {t['search_text']};
            border: 1px solid rgba(255,255,255,25);
            border-radius: 10px; padding: 6px 10px; font-size: 12px;
        }}
        QDateEdit::drop-down {{ border: none; width: 18px; }}
        QDateEdit::down-arrow {{
            image: none; border-left: 4px solid transparent;
            border-right: 4px solid transparent;
            border-top: 6px solid {t['text_dim']};
            width: 0; height: 0; margin-right: 6px;
        }}

        QTextEdit {{
            background-color: {t['lyrics_bg']};
            color: {t['lyrics_text']};
            border: 1px solid rgba(255,255,255,25);
            border-radius: 12px; padding: 10px; font-size: 12px;
            selection-background-color: {t['accent']};
            selection-color: #ffffff;
        }}
        QTextEdit:focus {{ border: 1px solid {t['accent']}; }}

        QScrollArea {{ border: none; background: transparent; }}
        QScrollArea > QWidget > QWidget {{ background: transparent; }}
        QScrollBar:vertical {{ background: transparent; width: 8px; margin: 2px; }}
        QScrollBar::handle:vertical {{
            background: rgba(255,255,255,50); border-radius: 4px; min-height: 30px;
        }}
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
        QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{ background: none; }}

        QMenu {{
            background-color: rgba({r},{g},{b},245);
            color: {t['text']};
            border: 1px solid rgba(255,255,255,25);
            border-radius: 10px; padding: 6px;
        }}
        QMenu::item {{ padding: 8px 22px; border-radius: 6px; }}
        QMenu::item:selected {{ background-color: {t['accent']}; color: #ffffff; }}
        QMenu::separator {{ height: 1px; background: rgba(255,255,255,25); margin: 4px 10px; }}

        QGroupBox {{
            background-color: rgba({r},{g},{b},140);
            border: 1px solid rgba(255,255,255,22);
            border-radius: 12px;
            margin-top: 14px;
            padding-top: 4px;
            font-weight: bold;
            color: {t['accent']};
        }}
        QGroupBox::title {{
            subcontrol-origin: margin;
            subcontrol-position: top left;
            left: 14px; padding: 0 8px; color: {t['accent']};
        }}

        QToolTip {{
            background-color: {t['accent']}; color: white;
            border: none; border-radius: 6px; padding: 4px 8px;
        }}
        QDialog {{ background-color: rgba({r},{g},{b},245); }}
        """

    def apply_theme(self):
        self._row_style_cache.clear()
        self.setStyleSheet(self.build_qss())
        for real_idx, _, name_btn, heart_btn in self.track_rows:
            if 0 <= real_idx < len(self.playlist):
                self._style_track_row(real_idx, name_btn, heart_btn,
                                      self.playlist[real_idx])
        self.theme_btn.setText(self.theme()["name"])
        self._update_net_button()

    def _set_theme(self, key):
        if key in THEMES:
            self._theme_name = key
            self.apply_theme()
            self.save_config()

    def _open_theme_menu(self):
        menu = QMenu(self)
        for key, t in THEMES.items():
            a = menu.addAction(t["name"])
            a.setCheckable(True)
            a.setChecked(key == self._theme_name)
            a.triggered.connect(lambda checked=False, k=key: self._set_theme(k))
        menu.addSeparator()
        menu.addAction("⚙  Настройки…", self._open_color_dialog)
        menu.exec(self.theme_btn.mapToGlobal(
            QPoint(0, self.theme_btn.height() + 2)))

    def _open_color_dialog(self):
        ColorSettingsDialog(self).exec()

    def _open_reports(self):
        ReportsDialog(self).exec()

    # ------------------------------------------------------------------
    #  Интернет-режим + Genius
    # ------------------------------------------------------------------
    def _toggle_internet(self):
        self.internet_enabled = not self.internet_enabled
        self._update_net_button()
        self.save_config()
        self.status_label.setText(
            "Интернет включён — доступна функция «Найти на Genius»"
            if self.internet_enabled
            else "Интернет отключён — функция «Найти на Genius» скрыта")

    def _update_net_button(self):
        if not hasattr(self, "net_btn"):
            return
        self.net_btn.setText("●" if self.internet_enabled else "○")
        self.net_btn.setProperty("online", "true" if self.internet_enabled else "false")
        self.net_btn.style().unpolish(self.net_btn)
        self.net_btn.style().polish(self.net_btn)
        self.net_btn.setToolTip(
            "Интернет включён — клик чтобы отключить"
            if self.internet_enabled
            else "Интернет отключён — клик чтобы включить")

    def _search_genius(self, path):
        name = self._display_name(path)
        if name.lower().endswith((".mp3", ".wav", ".ogg", ".flac", ".m4a")):
            name = os.path.splitext(name)[0]
        artist = self._display_artist(path)
        query = f"{name} {artist}".strip() if artist else name
        try:
            webbrowser.open(f"https://genius.com/search?q={quote_plus(query)}")
            self.status_label.setText(f"Genius: {query}")
        except Exception as e:
            QMessageBox.warning(self, "Ошибка",
                                f"Не удалось открыть браузер:\n{e}")

    # ------------------------------------------------------------------
    #  Длительность
    # ------------------------------------------------------------------
    def _get_duration(self, path):
        if path in self._duration_cache:
            return self._duration_cache[path]
        dur = 0.0
        if HAS_MUTAGEN:
            try:
                audio = MutagenFile(path)
                if audio and audio.info:
                    dur = float(audio.info.length)
            except Exception:
                pass
        self._duration_cache[path] = dur
        return dur

    @staticmethod
    def _format_total_duration(seconds):
        if seconds <= 0:
            return ""
        s = int(seconds)
        h, rem = divmod(s, 3600)
        m = rem // 60
        if h > 0:
            return f"{h} ч {m} мин"
        if m > 0:
            return f"{m} мин"
        return f"{s} сек"

    def _schedule_duration_update(self, base_text):
        self._duration_gen += 1
        gen = self._duration_gen

        if all(p in self._duration_cache for p in self.playlist):
            dur_str = self._format_total_duration(
                sum(self._duration_cache[p] for p in self.playlist))
            if dur_str:
                base_text += f"  ·  {dur_str}"
            self.playlist_count.setText(base_text)
            return

        self._duration_base  = base_text
        self._duration_idx   = 0
        self._duration_total = 0.0
        self.playlist_count.setText(base_text + "  ·  считаю длительность…")
        QTimer.singleShot(0, lambda: self._duration_chunk(gen))

    def _duration_chunk(self, gen):
        if gen != self._duration_gen:
            return
        total = len(self.playlist)
        end = min(self._duration_idx + 25, total)
        for i in range(self._duration_idx, end):
            self._duration_total += self._get_duration(self.playlist[i])
        self._duration_idx = end
        if gen != self._duration_gen:
            return
        if end >= total:
            dur_str = self._format_total_duration(self._duration_total)
            text = self._duration_base
            if dur_str:
                text += f"  ·  {dur_str}"
            self.playlist_count.setText(text)
        else:
            partial = self._format_total_duration(self._duration_total)
            text = self._duration_base + "  ·  считаю"
            if partial:
                text += f" ({partial})"
            self.playlist_count.setText(text)
            QTimer.singleShot(0, lambda: self._duration_chunk(gen))

    # ------------------------------------------------------------------
    #  Панель «Текст»
    # ------------------------------------------------------------------
    def _build_lyrics_panel(self):
        self.lyrics_panel = QFrame()
        self.lyrics_panel.setObjectName("glassPanel")
        self.lyrics_panel.setMinimumWidth(320)
        self.lyrics_panel.setMaximumWidth(560)

        ll = QVBoxLayout(self.lyrics_panel)
        ll.setContentsMargins(16, 16, 16, 16)
        ll.setSpacing(8)

        header = QHBoxLayout()
        self.lyrics_title = QLabel("Текст")
        ft = self.lyrics_title.font(); ft.setPointSize(13); ft.setBold(True)
        self.lyrics_title.setFont(ft)
        self.lyrics_title.setWordWrap(True)
        header.addWidget(self.lyrics_title, 1)

        close_btn = self._btn("✕", "icon", fixed=(32, 32), tip="Закрыть текст")
        close_btn.clicked.connect(self._close_lyrics)
        header.addWidget(close_btn)

        ll.addLayout(header)

        self.lyrics_edit = QTextEdit()
        self.lyrics_edit.setPlaceholderText(
            "Скопируйте с genius или найдите в интернете")
        self.lyrics_edit.setFont(QFont("Segoe UI", 11))
        self.lyrics_edit.textChanged.connect(self._on_lyrics_changed)
        ll.addWidget(self.lyrics_edit, 1)

    def _open_current_lyrics(self):
        if not (0 <= self.current_index < len(self.playlist)):
            self.status_label.setText(
                "Нет активного трека — выбери и запусти, затем нажми «Текст»")
            return
        path = self.playlist[self.current_index]
        if self.lyrics_panel.isVisible() and self._lyrics_path == path:
            self._close_lyrics()
        else:
            self._open_lyrics(path)

    def _open_lyrics(self, path):
        if self._lyrics_path == path and self.lyrics_panel.isVisible():
            return
        self._lyrics_save_timer.stop()
        if self._lyrics_path and self._lyrics_path != path:
            self._save_lyrics_now()
        self._lyrics_path = path
        self.lyrics_title.setText(f"Текст: {self._display_name(path)}")
        text = self.metadata.get(path, {}).get("lyrics", "")
        self.lyrics_edit.blockSignals(True)
        self.lyrics_edit.setPlainText(text)
        self.lyrics_edit.blockSignals(False)
        if not self.lyrics_panel.isVisible():
            self.lyrics_panel.show()
            if self.width() < 1100:
                self.resize(1200, self.height())

    def _close_lyrics(self):
        self._lyrics_save_timer.stop()
        self._save_lyrics_now()
        self._lyrics_path = None
        self.lyrics_panel.hide()

    def _on_lyrics_changed(self):
        if self._lyrics_path:
            self._lyrics_save_timer.start()

    def _save_lyrics_now(self):
        if not self._lyrics_path or not hasattr(self, "lyrics_edit"):
            return
        path = self._lyrics_path
        text = self.lyrics_edit.toPlainText().strip()
        current = self.metadata.get(path, {}).get("lyrics", "")
        if text == current:
            return
        if text:
            self.metadata.setdefault(path, {})["lyrics"] = text
        else:
            if path in self.metadata:
                self.metadata[path].pop("lyrics", None)
                if not self.metadata[path]:
                    del self.metadata[path]
        self.save_config()

    # ------------------------------------------------------------------
    #  UI
    # ------------------------------------------------------------------
    def _btn(self, text, obj="secondary", fixed=None, size=None, tip=None):
        b = QPushButton(text)
        b.setObjectName(obj)
        if fixed:
            b.setFixedSize(*fixed)
        f = QFont()
        if obj in ("icon", "like", "play", "net", "liked_btn"):
            f.setFamily("Segoe UI Symbol")
            f.setPointSize(size if size else 11)
            f.setWeight(QFont.Bold)
            b.setFont(f)
        elif size:
            f.setFamily("Segoe UI")
            f.setPointSize(size)
            b.setFont(f)
        if tip:
            b.setToolTip(tip)
        return b

    def build_ui(self):
        outer = QHBoxLayout(self.central)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)
        outer.addStretch(1)

        content = QWidget()
        content.setMaximumWidth(CONTENT_MAX_WIDTH)
        outer.addWidget(content, 3)

        self._build_lyrics_panel()
        outer.addWidget(self.lyrics_panel, 2)
        self.lyrics_panel.hide()

        outer.addStretch(1)

        root = QVBoxLayout(content)
        root.setContentsMargins(22, 18, 22, 14)
        root.setSpacing(10)

        # --- Шапка ---
        header = QWidget()
        hl = QHBoxLayout(header); hl.setContentsMargins(0, 0, 0, 0)
        title = QLabel("♪  Music Player")
        f = title.font(); f.setPointSize(22); f.setBold(True); title.setFont(f)
        hl.addWidget(title)

        hl.addSpacing(16)
        self.reports_btn = self._btn("📊  Отчёты", "secondary")
        self.reports_btn.setFixedHeight(36)
        self.reports_btn.clicked.connect(self._open_reports)
        self.reports_btn.setToolTip("Итоги дня / недели / месяца")
        hl.addWidget(self.reports_btn)

        hl.addStretch()

        self.theme_btn = self._btn(self.theme()["name"], "secondary")
        self.theme_btn.clicked.connect(self._open_theme_menu)
        hl.addWidget(self.theme_btn)

        self.color_btn = self._btn("⚙", "icon", fixed=(42, 38),
                                   tip="Настройки")
        self.color_btn.clicked.connect(self._open_color_dialog)
        hl.addWidget(self.color_btn)

        self.net_btn = self._btn("●", "net", fixed=(42, 38),
                                 tip="Интернет включён — клик чтобы отключить")
        self.net_btn.clicked.connect(self._toggle_internet)
        hl.addWidget(self.net_btn)

        root.addWidget(header)

        # --- Now Playing ---
        self.now_card = QFrame(); self.now_card.setObjectName("glassPanel")
        nl = QVBoxLayout(self.now_card)
        nl.setContentsMargins(20, 20, 20, 16); nl.setSpacing(14)

        top = QWidget()
        tl = QHBoxLayout(top); tl.setContentsMargins(0, 0, 0, 0); tl.setSpacing(20)

        self.cover_label = ClickableLabel()
        self.cover_label.setFixedSize(COVER_SIZE, COVER_SIZE)
        self.cover_label.setCursor(Qt.PointingHandCursor)
        self.cover_label.setToolTip("Клик — сменить обложку")
        self.cover_label.clicked.connect(self._cover_menu)
        tl.addWidget(self.cover_label, 0, Qt.AlignTop)

        info = QWidget()
        il = QVBoxLayout(info); il.setContentsMargins(0, 0, 0, 0); il.setSpacing(4)

        self.now_title = QLabel("—")
        ft = self.now_title.font(); ft.setPointSize(16); ft.setBold(True)
        self.now_title.setFont(ft); self.now_title.setWordWrap(True)
        il.addWidget(self.now_title)

        self.now_artist = QLabel("")
        self.now_artist.setObjectName("dim")
        il.addWidget(self.now_artist)

        now_actions = QHBoxLayout()
        now_actions.setContentsMargins(0, 4, 0, 0)
        now_actions.setSpacing(4)
        self.now_lyrics_btn = self._btn("📄  Текст", "secondary")
        self.now_lyrics_btn.setFixedHeight(28)
        self.now_lyrics_btn.clicked.connect(self._open_current_lyrics)
        self.now_lyrics_btn.setToolTip("Открыть / закрыть текст текущего трека")
        now_actions.addWidget(self.now_lyrics_btn)
        now_actions.addStretch()
        il.addLayout(now_actions)

        il.addSpacing(4)

        self.progress = ClickableSlider(Qt.Horizontal)
        self.progress.setRange(0, 0)
        self.progress.sliderPressed.connect(lambda: setattr(self, "_dragging_seek", True))
        self.progress.sliderReleased.connect(self._on_seek_release)
        self.progress.sliderMoved.connect(self._on_seek_move)
        il.addWidget(self.progress)

        self.time_label = QLabel("0:00 / 0:00")
        self.time_label.setObjectName("dim")
        il.addWidget(self.time_label)
        il.addStretch()
        tl.addWidget(info, 1)
        nl.addWidget(top)

        ctrl = QWidget()
        cl = QHBoxLayout(ctrl); cl.setContentsMargins(0, 0, 0, 0); cl.setSpacing(6)

        self.btn_prev = self._btn(G_PREV, "icon", fixed=(52, 44))
        self.btn_prev.clicked.connect(self.prev)
        cl.addWidget(self.btn_prev)

        self.btn_play = self._btn(G_PLAY, "play", fixed=(64, 52))
        self.btn_play.clicked.connect(self.toggle_play)
        cl.addWidget(self.btn_play)

        self.btn_stop = self._btn(G_STOP, "icon", fixed=(52, 44))
        self.btn_stop.clicked.connect(self.stop)
        cl.addWidget(self.btn_stop)

        self.btn_next = self._btn(G_NEXT, "icon", fixed=(52, 44))
        self.btn_next.clicked.connect(self.next)
        cl.addWidget(self.btn_next)

        cl.addSpacing(8)
        vol_icon = QLabel("🔊")
        fv = vol_icon.font(); fv.setPointSize(13); vol_icon.setFont(fv)
        cl.addWidget(vol_icon)

        self.volume_value_label = QLabel(str(self._saved_vol))
        self.volume_value_label.setObjectName("volval")
        self.volume_value_label.setFixedWidth(30)
        self.volume_value_label.setAlignment(Qt.AlignCenter)
        cl.addWidget(self.volume_value_label)

        self.volume_slider = ClickableSlider(Qt.Horizontal)
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setMaximumWidth(VOLUME_MAX_WIDTH)
        self.volume_slider.setMinimumWidth(120)
        self.volume_slider.valueChanged.connect(self._on_volume_change)
        cl.addWidget(self.volume_slider)

        cl.addStretch()
        nl.addWidget(ctrl)
        root.addWidget(self.now_card)

        # --- Панель плейлистов ---
        plbar = QWidget()
        pll = QHBoxLayout(plbar); pll.setContentsMargins(0, 0, 0, 0); pll.setSpacing(6)

        self.liked_btn = self._btn(G_HEART, "icon", fixed=(42, 38),
                                   tip="Понравившиеся")
        self.liked_btn.setObjectName("liked_btn")
        self.liked_btn.setFont(self._icon_font(11))
        self.liked_btn.clicked.connect(lambda: self._switch_playlist(DEFAULT_LIKED))
        pll.addWidget(self.liked_btn)

        pll.addSpacing(6)
        self._plbar_sep = QFrame()
        self._plbar_sep.setObjectName("vsep")
        self._plbar_sep.setFixedSize(1, 26)
        pll.addWidget(self._plbar_sep)
        pll.addSpacing(6)

        self.playlist_btn = self._btn(self.active_playlist, "secondary")
        self.playlist_btn.clicked.connect(self._open_playlist_menu)
        pll.addWidget(self.playlist_btn)

        self.btn_new_pl = self._btn("＋", "icon", fixed=(42, 38),
                                    tip="Новый плейлист")
        self.btn_new_pl.clicked.connect(self._create_playlist)
        pll.addWidget(self.btn_new_pl)

        self.btn_ren_pl = self._btn("✎", "icon", fixed=(42, 38),
                                    tip="Переименовать")
        self.btn_ren_pl.clicked.connect(self._rename_playlist)
        pll.addWidget(self.btn_ren_pl)

        self.btn_del_pl = self._btn("✕", "icon", fixed=(42, 38),
                                    tip="Удалить")
        self.btn_del_pl.clicked.connect(self._delete_playlist)
        pll.addWidget(self.btn_del_pl)

        pll.addStretch()
        self.playlist_count = QLabel("0 треков")
        self.playlist_count.setObjectName("stats")
        pll.addWidget(self.playlist_count)
        root.addWidget(plbar)

        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("🔍 Поиск по названию или исполнителю…")
        self.search_edit.setClearButtonEnabled(True)
        self.search_edit.textChanged.connect(self._schedule_filter)
        root.addWidget(self.search_edit)

        self.playlist_card = QFrame(); self.playlist_card.setObjectName("glassPanel")
        pcl = QVBoxLayout(self.playlist_card)
        pcl.setContentsMargins(10, 10, 10, 10)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.NoFrame)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.track_container = QWidget()
        self.track_layout = QVBoxLayout(self.track_container)
        self.track_layout.setContentsMargins(2, 2, 2, 2)
        self.track_layout.setSpacing(2)
        self.track_layout.addStretch()
        self.scroll.setWidget(self.track_container)
        pcl.addWidget(self.scroll)
        root.addWidget(self.playlist_card, 1)

        bottom = QWidget()
        bl = QHBoxLayout(bottom); bl.setContentsMargins(0, 0, 0, 0); bl.setSpacing(6)

        self.btn_files = self._btn("＋  Файлы")
        self.btn_files.clicked.connect(self.add_files)
        bl.addWidget(self.btn_files)

        self.btn_folder = self._btn("📁  Папка")
        self.btn_folder.clicked.connect(self.add_folder)
        bl.addWidget(self.btn_folder)

        self.btn_clear = self._btn("Очистить")
        self.btn_clear.clicked.connect(self.clear_playlist)
        bl.addWidget(self.btn_clear)

        bl.addStretch()
        root.addWidget(bottom)

        self.status_label = QLabel("Ничего не играет")
        self.status_label.setObjectName("dim")
        root.addWidget(self.status_label)

        self.cover_label.setPixmap(self._cover_pixmap(None))

    # ------------------------------------------------------------------
    #  Меню
    # ------------------------------------------------------------------
    def _open_playlist_menu(self):
        menu = QMenu(self)
        names = [DEFAULT_LIKED] + [n for n in self.playlists if n != DEFAULT_LIKED]
        for name in names:
            a = menu.addAction(name)
            a.setCheckable(True)
            a.setChecked(name == self.active_playlist)
            a.triggered.connect(lambda checked=False, n=name: self._switch_playlist(n))
        menu.addSeparator()
        menu.addAction("＋  Новый плейлист", self._create_playlist)
        menu.addAction("✎  Переименовать", self._rename_playlist)
        menu.addAction("✕  Удалить", self._delete_playlist)
        menu.exec(self.playlist_btn.mapToGlobal(
            QPoint(0, self.playlist_btn.height() + 2)))

    def _track_context(self, real_index, global_pos):
        if not (0 <= real_index < len(self.playlist)):
            return
        path = self.playlist[real_index]
        liked = path in self.playlists[DEFAULT_LIKED]
        menu = QMenu(self)
        menu.addAction("▶  Играть", lambda: self.play_index(real_index))
        menu.addAction("✎  Информация о треке…", lambda: self._edit_track_info(path))
        menu.addAction("📄  Текст", lambda: self._open_lyrics(path))
        menu.addAction("🖼  Сменить обложку…", lambda: self._change_cover(path))
        menu.addAction("↺  Сбросить оформление", lambda: self._reset_track_meta(path))
        if self.internet_enabled:
            menu.addSeparator()
            menu.addAction("🎵  Найти на Genius", lambda: self._search_genius(path))
        menu.addSeparator()
        menu.addAction(("💔  Убрать из избранного" if liked else "❤  В понравившиеся"),
                       lambda: self._toggle_like(path))
        menu.addSeparator()
        menu.addAction("✕  Удалить из плейлиста", lambda: self._remove_track(real_index))
        menu.exec(global_pos)

    def _cover_menu(self):
        if not (0 <= self.current_index < len(self.playlist)):
            self.status_label.setText(
                "Нет активного трека — запусти воспроизведение, затем кликни по обложке")
            return
        path = self.playlist[self.current_index]
        menu = QMenu(self)
        menu.addAction("🖼  Сменить обложку…", lambda: self._change_cover(path))
        if self.metadata.get(path, {}).get("cover"):
            menu.addAction("↺  Убрать обложку", lambda: self._remove_cover(path))
        menu.addSeparator()
        menu.addAction("🎤  Информация о треке…", lambda: self._edit_track_info(path))
        menu.addAction("📄  Текст", lambda: self._open_lyrics(path))
        menu.exec(QCursor.pos())

    # ------------------------------------------------------------------
    #  Фон
    # ------------------------------------------------------------------
    def _set_background(self):
        f, _ = QFileDialog.getOpenFileName(
            self, "Выберите фоновое изображение", "",
            "Изображения (*.png *.jpg *.jpeg *.webp *.bmp);;Все файлы (*)")
        if not f:
            return
        self.background_path = f
        self.central.set_background(f)
        self.save_config()

    def _clear_background(self):
        self.background_path = ""
        self.central.set_background("")
        self.save_config()

    # ------------------------------------------------------------------
    #  Плейлисты
    # ------------------------------------------------------------------
    def _switch_playlist(self, name):
        if name not in self.playlists or name == self.active_playlist:
            return
        self.stop()
        if self._lyrics_path:
            self._lyrics_save_timer.stop()
            self._save_lyrics_now()
            self._lyrics_path = None
            self.lyrics_panel.hide()
        self.active_playlist = name
        self.playlist = self.playlists[name]
        self.current_index = -1
        self.playlist_btn.setText(name)
        self.search_edit.clear()
        self.rebuild_playlist()
        self.now_title.setText("—")
        self.now_artist.setText("")
        self.cover_label.setPixmap(self._cover_pixmap(None))
        self.progress.setRange(0, 0)
        self.progress.setValue(0)
        self.time_label.setText("0:00 / 0:00")
        self.save_config()

    def _create_playlist(self):
        name, ok = QInputDialog.getText(self, "Новый плейлист", "Название:")
        if not ok or not name.strip():
            return
        name = name.strip()
        if name == DEFAULT_LIKED:
            QMessageBox.warning(self, "Внимание", "Это имя зарезервировано")
            return
        if name in self.playlists:
            QMessageBox.warning(self, "Внимание", "Плейлист с таким названием уже есть")
            return
        self.playlists[name] = []
        self.save_config()
        self._switch_playlist(name)

    def _rename_playlist(self):
        if self.active_playlist == DEFAULT_LIKED:
            QMessageBox.information(self, "Инфо",
                                    "Плейлист «Понравившиеся» переименовать нельзя")
            return
        old = self.active_playlist
        new, ok = QInputDialog.getText(self, "Переименовать",
                                        "Новое название:", text=old)
        if not ok or not new.strip() or new.strip() == old:
            return
        new = new.strip()
        if new in self.playlists or new == DEFAULT_LIKED:
            QMessageBox.warning(self, "Внимание", "Имя занято")
            return
        new_dict = {}
        for k, v in self.playlists.items():
            new_dict[new if k == old else k] = v
        self.playlists = new_dict
        self.active_playlist = new
        self.playlist = self.playlists[new]
        self.playlist_btn.setText(new)
        self.save_config()

    def _delete_playlist(self):
        if self.active_playlist == DEFAULT_LIKED:
            QMessageBox.information(self, "Инфо",
                                    "Плейлист «Понравившиеся» удалить нельзя")
            return
        if len(self.playlists) <= 2:
            QMessageBox.warning(self, "Внимание",
                                "Нельзя удалить последний обычный плейлист")
            return
        name = self.active_playlist
        if QMessageBox.question(self, "Удалить",
                                f"Удалить плейлист «{name}»?") != QMessageBox.Yes:
            return
        del self.playlists[name]
        self.active_playlist = next(k for k in self.playlists if k != DEFAULT_LIKED)
        self.playlist = self.playlists[self.active_playlist]
        self.current_index = -1
        self.playlist_btn.setText(self.active_playlist)
        self.search_edit.clear()
        self.rebuild_playlist()
        self.save_config()

    # ------------------------------------------------------------------
    #  Поиск
    # ------------------------------------------------------------------
    def _schedule_filter(self):
        self._filter_timer.start()

    def _matches(self, path, query):
        if not query:
            return True
        name = self._display_name(path).lower()
        artist = self._display_artist(path).lower()
        return query in name or query in artist

    # ------------------------------------------------------------------
    #  Список треков
    # ------------------------------------------------------------------
    def _get_row_style(self, is_current):
        key = (self._theme_name, is_current)
        cached = self._row_style_cache.get(key)
        if cached is not None:
            return cached
        t = self.theme()
        bg = t["row_current"] if is_current else "transparent"
        fg = t["accent"] if is_current else t["text"]
        ss = (f"QPushButton {{ background: {bg}; color: {fg}; text-align: left; "
              f"padding: 8px 14px; border-radius: 8px; font-size: 12px; border: none; }}"
              f"QPushButton:hover {{ background: {t['row_hover']}; }}")
        self._row_style_cache[key] = ss
        return ss

    def rebuild_playlist(self):
        while self.track_layout.count() > 0:
            item = self.track_layout.takeAt(0)
            w = item.widget()
            if w:
                w.setParent(None)
                w.deleteLater()
        self.track_rows = []

        query = self.search_edit.text().strip().lower()

        for real_i, path in enumerate(self.playlist):
            if not self._matches(path, query):
                continue

            row = QWidget()
            h = QHBoxLayout(row); h.setContentsMargins(0, 0, 0, 0); h.setSpacing(4)

            name_btn = QPushButton()
            name_btn.setCursor(Qt.PointingHandCursor)
            name_btn.setMinimumHeight(40)
            name_btn.clicked.connect(lambda _, idx=real_i: self.play_index(idx))
            name_btn.setContextMenuPolicy(Qt.CustomContextMenu)
            name_btn.customContextMenuRequested.connect(
                lambda pos, idx=real_i, b=name_btn:
                self._track_context(idx, b.mapToGlobal(pos)))

            heart_btn = QPushButton(G_HEART_EMPTY)
            heart_btn.setObjectName("like")
            heart_btn.setFixedSize(40, 40)
            heart_btn.setCursor(Qt.PointingHandCursor)
            heart_btn.setToolTip("Добавить/убрать из избранного")
            heart_btn.setFont(self._icon_font(14))
            heart_btn.clicked.connect(lambda _, p=path: self._toggle_like(p))

            self._style_track_row(real_i, name_btn, heart_btn, path)

            h.addWidget(name_btn, 1)
            h.addWidget(heart_btn, 0)
            self.track_layout.addWidget(row)
            self.track_rows.append((real_i, row, name_btn, heart_btn))

        self.track_layout.addStretch()

        n = len(self.track_rows)
        total = len(self.playlist)
        base = (f"{n} из {total}" if query
                else f"{total} трек" + ("" if total == 1 else "ов"))
        self._schedule_duration_update(base)

    def _style_track_row(self, real_index, name_btn, heart_btn, path):
        is_current = (real_index == self.current_index)
        name = self._display_name(path)
        artist = self._display_artist(path)
        name_btn.setText(f"{name}   —   {artist}" if artist else name)
        name_btn.setStyleSheet(self._get_row_style(is_current))

        liked = path in self.playlists[DEFAULT_LIKED]
        heart_btn.setText(G_HEART if liked else G_HEART_EMPTY)
        heart_btn.setProperty("liked", "true" if liked else "false")
        heart_btn.style().unpolish(heart_btn)
        heart_btn.style().polish(heart_btn)

    def _refresh_highlights(self):
        for real_idx, _, name_btn, heart_btn in self.track_rows:
            if 0 <= real_idx < len(self.playlist):
                self._style_track_row(real_idx, name_btn, heart_btn,
                                      self.playlist[real_idx])

    # ------------------------------------------------------------------
    #  Метаданные
    # ------------------------------------------------------------------
    def _display_name(self, path):
        return self.metadata.get(path, {}).get("display_name") or os.path.basename(path)

    def _display_artist(self, path):
        meta = self.metadata.get(path, {})
        if "artist" in meta:
            return meta["artist"]
        return self._get_artist_from_tags(path)

    def _edit_track_info(self, path):
        cur_name   = self._display_name(path)
        cur_artist = self._display_artist(path)
        dlg = TrackInfoDialog(self, cur_name, cur_artist)
        if dlg.exec() != QDialog.Accepted:
            return
        name, artist = dlg.values()
        meta = self.metadata.setdefault(path, {})
        if name:
            meta["display_name"] = name
        else:
            meta.pop("display_name", None)
        if artist:
            meta["artist"] = artist
        else:
            meta.pop("artist", None)
        if not meta:
            del self.metadata[path]
        self.save_config()
        self.rebuild_playlist()
        if 0 <= self.current_index < len(self.playlist) \
                and self.playlist[self.current_index] == path:
            self.now_title.setText(self._display_name(path))
            self.now_artist.setText(self._display_artist(path))
        if self._lyrics_path == path:
            self.lyrics_title.setText(f"Текст: {self._display_name(path)}")

    def _change_cover(self, path):
        f, _ = QFileDialog.getOpenFileName(
            self, "Выберите обложку", "",
            "Изображения (*.png *.jpg *.jpeg *.webp *.bmp);;Все файлы (*)")
        if not f:
            return
        self.metadata.setdefault(path, {})["cover"] = f
        self.save_config()
        if 0 <= self.current_index < len(self.playlist) \
                and self.playlist[self.current_index] == path:
            self.cover_label.setPixmap(self._cover_pixmap(path))

    def _remove_cover(self, path):
        if path in self.metadata and "cover" in self.metadata[path]:
            del self.metadata[path]["cover"]
            if not self.metadata[path]:
                del self.metadata[path]
            self.save_config()
            if 0 <= self.current_index < len(self.playlist) \
                    and self.playlist[self.current_index] == path:
                self.cover_label.setPixmap(self._cover_pixmap(path))

    def _reset_track_meta(self, path):
        if path in self.metadata:
            del self.metadata[path]
            self.save_config()
            self.rebuild_playlist()
            if 0 <= self.current_index < len(self.playlist) \
                    and self.playlist[self.current_index] == path:
                self.cover_label.setPixmap(self._cover_pixmap(path))
                self.now_title.setText(self._display_name(path))
                self.now_artist.setText(self._display_artist(path))
            if self._lyrics_path == path:
                self.lyrics_edit.blockSignals(True)
                self.lyrics_edit.setPlainText("")
                self.lyrics_edit.blockSignals(False)

    def _remove_track(self, real_index):
        if not (0 <= real_index < len(self.playlist)):
            return
        path = self.playlist[real_index]
        if self._lyrics_path == path:
            self._close_lyrics()
        if real_index == self.current_index:
            self.stop()
            self.current_index = -1
        self.playlist.pop(real_index)
        if real_index < self.current_index:
            self.current_index -= 1
        self.save_config()
        self.rebuild_playlist()

    # ------------------------------------------------------------------
    #  Лайк
    # ------------------------------------------------------------------
    def _toggle_like(self, path):
        liked = self.playlists[DEFAULT_LIKED]
        if path in liked:
            liked.remove(path)
        else:
            liked.append(path)
        self.save_config()
        self.rebuild_playlist()

    # ------------------------------------------------------------------
    #  Обложки
    # ------------------------------------------------------------------
    def _round_pixmap(self, pix, radius):
        out = QPixmap(pix.size())
        out.fill(Qt.transparent)
        p = QPainter(out)
        p.setRenderHint(QPainter.Antialiasing)
        path = QPainterPath()
        path.addRoundedRect(0, 0, pix.width(), pix.height(), radius, radius)
        p.setClipPath(path)
        p.drawPixmap(0, 0, pix)
        p.end()
        return out

    def _default_cover(self):
        t = self.theme()
        pix = QPixmap(COVER_SIZE, COVER_SIZE)
        pix.fill(Qt.transparent)
        p = QPainter(pix)
        p.setRenderHint(QPainter.Antialiasing)
        grad = QLinearGradient(0, 0, COVER_SIZE, COVER_SIZE)
        grad.setColorAt(0, QColor(t["accent"]))
        grad.setColorAt(1, QColor(t["accent_hover"]))
        p.setBrush(QBrush(grad))
        p.setPen(Qt.NoPen)
        p.drawRoundedRect(0, 0, COVER_SIZE, COVER_SIZE, COVER_RADIUS, COVER_RADIUS)
        p.setPen(QColor(255, 255, 255, 220))
        f = QFont("Segoe UI Symbol", 46); f.setBold(True); p.setFont(f)
        p.drawText(0, 0, COVER_SIZE, COVER_SIZE, Qt.AlignCenter, "♪")
        p.end()
        return pix

    def _cover_pixmap(self, path):
        pix = None
        if path:
            meta = self.metadata.get(path, {})
            cover_path = meta.get("cover")
            if cover_path and os.path.isfile(cover_path):
                pix = QPixmap(cover_path)
            if (pix is None or pix.isNull()) and HAS_MUTAGEN:
                try:
                    audio = MutagenFile(path)
                    if audio:
                        data = None
                        tags = getattr(audio, "tags", None)
                        if tags and hasattr(tags, "getall"):
                            for k in tags.keys():
                                if str(k).startswith("APIC"):
                                    data = tags[k].data; break
                        elif hasattr(audio, "pictures"):
                            for pic in audio.pictures:
                                data = pic.data; break
                        if data:
                            p2 = QPixmap()
                            if p2.loadFromData(data):
                                pix = p2
                except Exception:
                    pass
        if pix is None or pix.isNull():
            return self._default_cover()
        pix = pix.scaled(COVER_SIZE, COVER_SIZE, Qt.KeepAspectRatioByExpanding,
                         Qt.SmoothTransformation)
        x = max(0, (pix.width() - COVER_SIZE) // 2)
        y = max(0, (pix.height() - COVER_SIZE) // 2)
        pix = pix.copy(x, y, COVER_SIZE, COVER_SIZE)
        return self._round_pixmap(pix, COVER_RADIUS)

    # ------------------------------------------------------------------
    #  Добавление / очистка
    # ------------------------------------------------------------------
    def add_files(self):
        files, _ = QFileDialog.getOpenFileNames(
            self, "Выберите аудио", "",
            "Аудио (*.mp3 *.wav *.ogg *.flac *.m4a);;Все файлы (*)")
        added = False
        for f in files:
            if f not in self.playlist:
                self.playlist.append(f); added = True
        if added:
            self.rebuild_playlist(); self.save_config()

    def add_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Выберите папку")
        if not folder:
            return
        exts = (".mp3", ".wav", ".ogg", ".flac", ".m4a")
        added = False
        for root_dir, _, files in os.walk(folder):
            for f in files:
                if f.lower().endswith(exts):
                    full = os.path.join(root_dir, f)
                    if full not in self.playlist:
                        self.playlist.append(full); added = True
        if added:
            self.rebuild_playlist(); self.save_config()

    def clear_playlist(self):
        name = self.active_playlist
        n = len(self.playlist)
        if n == 0:
            self.status_label.setText("Плейлист уже пуст")
            return
        msg = (f"Очистить «{name}»?\n\n"
               f"Будет удалено треков: {n}.\n"
               f"Файлы на диске останутся, но из плейлиста они исчезнут.")
        if QMessageBox.question(
                self, "Подтверждение очистки", msg,
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No) != QMessageBox.Yes:
            return
        if self._lyrics_path:
            self._close_lyrics()
        self.stop()
        self.playlist.clear()
        self.current_index = -1
        self.rebuild_playlist()
        self.save_config()
        self.status_label.setText("Плейлист очищен")

    # ------------------------------------------------------------------
    #  Воспроизведение
    # ------------------------------------------------------------------
    def play_index(self, real_index):
        if 0 <= real_index < len(self.playlist):
            self.current_index = real_index
            self.play_current()

    def play_current(self):
        if not (0 <= self.current_index < len(self.playlist)):
            return
        path = self.playlist[self.current_index]
        if not os.path.isfile(path):
            QMessageBox.critical(self, "Ошибка", f"Файл не найден:\n{path}")
            return

        # зафиксировать предыдущий трек
        if self._playing_path:
            self._commit_play()

        self._current_duration_ms = 0
        self.player.setSource(QUrl.fromLocalFile(path))
        self.player.play()
        self.cover_label.setPixmap(self._cover_pixmap(path))
        self.now_title.setText(self._display_name(path))
        self.now_artist.setText(self._display_artist(path))
        self.status_label.setText(f"Играет: {self._display_name(path)}")
        self._refresh_highlights()

        self._playing_path = path
        self._play_started_at = time.time()

        if self.lyrics_panel.isVisible() and self._lyrics_path != path:
            self._open_lyrics(path)

    def toggle_play(self):
        state = self.player.playbackState()
        if state == QMediaPlayer.PlayingState:
            self.player.pause()
        elif state == QMediaPlayer.PausedState:
            self.player.play()
        else:
            if self.playlist:
                if self.current_index < 0:
                    self.current_index = 0
                self.play_current()

    def stop(self):
        if self._playing_path:
            self._commit_play()
        self.player.stop()
        self.progress.setValue(0)
        self.time_label.setText(f"0:00 / {self._fmt(self.player.duration())}")
        self.status_label.setText("Остановлено")

    def next(self):
        if not self.playlist:
            return
        self.current_index = (self.current_index + 1) % len(self.playlist)
        self.play_current()

    def prev(self):
        if not self.playlist:
            return
        self.current_index = (self.current_index - 1) % len(self.playlist)
        self.play_current()

    def _update_volume_label(self, value):
        if hasattr(self, "volume_value_label"):
            self.volume_value_label.setText(str(int(value)))

    def _on_volume_change(self, value):
        self.audio.setVolume(value / 100)
        self._update_volume_label(value)
        self._volume_save_timer.start()

    # ------------------------------------------------------------------
    #  Перемотка / сигналы плеера
    # ------------------------------------------------------------------
    def _on_seek_release(self):
        self._dragging_seek = False
        self.player.setPosition(self.progress.value())

    def _on_seek_move(self, value):
        self.time_label.setText(
            f"{self._fmt(value)} / {self._fmt(self.player.duration())}")
        if not self._dragging_seek and self.player.duration() > 0:
            self.player.setPosition(value)

    def _on_position(self, pos):
        if not self._dragging_seek:
            self.progress.setValue(pos)
            self.time_label.setText(
                f"{self._fmt(pos)} / {self._fmt(self.player.duration())}")

    def _on_duration(self, dur):
        if dur > 0:
            self._current_duration_ms = dur
        self.progress.setRange(0, max(dur, 1))
        self.time_label.setText(f"{self._fmt(self.player.position())} / {self._fmt(dur)}")

    def _on_media_status(self, status):
        if status == QMediaPlayer.EndOfMedia:
            if not self._advancing:
                self._advancing = True
                # трек дослушан — фиксируем полностью.
                # duration() в этот момент часто = 0, поэтому
                # используем кэш. Если и кэш пуст — force=None,
                # тогда _commit_play возьмёт pos==0 → dur_sec.
                if self._playing_path:
                    dur_ms = self.player.duration()
                    if dur_ms <= 0:
                        dur_ms = self._current_duration_ms
                    force = dur_ms / 1000.0 if dur_ms > 0 else None
                    self._commit_play(force_dur=force)
                self.next()
                QTimer.singleShot(200, lambda: setattr(self, "_advancing", False))
        elif status == QMediaPlayer.InvalidMedia:
            self._log(f"invalid media: {self.player.source().toString()}")

    def _on_state(self, state):
        if state == QMediaPlayer.PlayingState:
            self.btn_play.setText(G_PAUSE)
        else:
            self.btn_play.setText(G_PLAY)

        if state == QMediaPlayer.PlayingState:
            if 0 <= self.current_index < len(self.playlist):
                self.status_label.setText(
                    f"Играет: {self._display_name(self.playlist[self.current_index])}")
        elif state == QMediaPlayer.PausedState:
            self.status_label.setText("Пауза")
        else:
            if self.status_label.text() not in ("Остановлено", "Ничего не играет"):
                self.status_label.setText("Остановлено")

    def _on_error(self, err, msg):
        self._log(f"player error: {err} {msg}")
        if err != QMediaPlayer.NoError and msg:
            self.status_label.setText(f"Ошибка: {msg}")

    # ------------------------------------------------------------------
    #  Утилиты
    # ------------------------------------------------------------------
    @staticmethod
    def _icon_font(pt):
        f = QFont("Segoe UI Symbol")
        f.setPointSize(pt)
        f.setWeight(QFont.Bold)
        return f

    def _get_artist_from_tags(self, path):
        if not HAS_MUTAGEN:
            return ""
        try:
            audio = MutagenFile(path)
            tags = getattr(audio, "tags", None) if audio else None
            if not tags:
                return ""
            for key in ("TPE1", "artist", "ARTIST", "©ART"):
                if key in tags:
                    val = tags[key]
                    if hasattr(val, "text"):
                        return str(val.text[0])
                    return str(val)
        except Exception:
            pass
        return ""

    @staticmethod
    def _fmt(ms):
        try:
            s = max(0, int(float(ms) / 1000))
        except Exception:
            s = 0
        m, s = divmod(s, 60)
        return f"{m}:{s:02d}"

    def restore_status(self):
        if self.playlist:
            self.status_label.setText(
                f"Загружено: {len(self.playlist)} · ПКМ по треку — оформление")
        else:
            self.status_label.setText("Пусто · добавь треки и нажми ▶")

    def closeEvent(self, event):
        try:
            if self._playing_path:
                self._commit_play()
        except Exception:
            pass
        try:
            self._volume_save_timer.stop()
            self._lyrics_save_timer.stop()
            self._save_lyrics_now()
        except Exception:
            pass
        try:
            self.save_config()
        except Exception:
            pass
        event.accept()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    window = MusicPlayer()
    window.show()
    sys.exit(app.exec())