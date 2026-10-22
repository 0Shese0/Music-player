import sys
import os
import json
import time
import math
import random
import webbrowser
from datetime import datetime, timedelta
from pathlib import Path
from urllib.parse import quote_plus, urlencode

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QSlider, QScrollArea, QMenu, QFileDialog,
    QMessageBox, QFrame, QLineEdit, QDialog, QFormLayout, QColorDialog,
    QInputDialog, QStyle, QStyleOptionSlider, QTextEdit, QTextBrowser,
    QGroupBox, QButtonGroup, QDateEdit, QGridLayout, QComboBox,
    QStackedWidget, QCheckBox,
)
from PySide6.QtCore import (
    Qt, QTimer, QUrl, QPoint, QPointF, Signal, QDate, QRect, QObject,
)
from PySide6.QtGui import (
    QPixmap, QPainter, QPainterPath, QColor, QFont,
    QLinearGradient, QRadialGradient, QBrush, QCursor,
    QPen, QPolygonF,
)
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput
from PySide6.QtNetwork import QNetworkAccessManager, QNetworkRequest, QNetworkReply

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
        "name": "🌙 Тёмная",
        "accent": "#7c5cff", "accent_hover": "#9d7fff",
        "panel_rgb": (22, 22, 28), "panel_alpha": 195,
        "text": "#f0f0f5", "text_dim": "#8a8a95",
        "row_current": "rgba(124, 92, 255, 70)",
        "row_hover": "rgba(255, 255, 255, 25)",
        "surface": "rgba(255, 255, 255, 18)",
        "lyrics_text": "#e8e8f0", "lyrics_bg": "#0e0e12",
        "search_text": "#f0f0f5", "search_bg": "#1a1a22",
        "liked_bg": "#7c5cff", "stats_text": "#8a8a95",
        "wave_accent": "#7c5cff", "wave_bg": "#0e0e12",
    },
    "light": {
        "name": "☀️ Светлая",
        "accent": "#5b47d6", "accent_hover": "#7c6bf0",
        "panel_rgb": (255, 255, 255), "panel_alpha": 200,
        "text": "#1a1a20", "text_dim": "#6a6a75",
        "row_current": "rgba(91, 71, 214, 55)",
        "row_hover": "rgba(0, 0, 0, 20)",
        "surface": "rgba(0, 0, 0, 15)",
        "lyrics_text": "#1a1a20", "lyrics_bg": "#ffffff",
        "search_text": "#1a1a20", "search_bg": "#f2f2f7",
        "liked_bg": "#5b47d6", "stats_text": "#6a6a75",
        "wave_accent": "#5b47d6", "wave_bg": "#e8e8f2",
    },
    "blue": {
        "name": "🌊 Синяя",
        "accent": "#3f88c5", "accent_hover": "#5ba0dd",
        "panel_rgb": (14, 30, 48), "panel_alpha": 195,
        "text": "#e0eaf5", "text_dim": "#7a90a8",
        "row_current": "rgba(63, 136, 197, 75)",
        "row_hover": "rgba(255, 255, 255, 22)",
        "surface": "rgba(255, 255, 255, 18)",
        "lyrics_text": "#dceaf5", "lyrics_bg": "#081420",
        "search_text": "#dceaf5", "search_bg": "#0e2236",
        "liked_bg": "#3f88c5", "stats_text": "#7a90a8",
        "wave_accent": "#5ba0dd", "wave_bg": "#081420",
    },
    "green": {
        "name": "🌿 Зелёная",
        "accent": "#4caf50", "accent_hover": "#66bb6a",
        "panel_rgb": (16, 32, 18), "panel_alpha": 195,
        "text": "#e0f0e0", "text_dim": "#7a9a7a",
        "row_current": "rgba(76, 175, 80, 75)",
        "row_hover": "rgba(255, 255, 255, 22)",
        "surface": "rgba(255, 255, 255, 18)",
        "lyrics_text": "#e0f0e0", "lyrics_bg": "#0a180c",
        "search_text": "#e0f0e0", "search_bg": "#142614",
        "liked_bg": "#4caf50", "stats_text": "#7a9a7a",
        "wave_accent": "#66bb6a", "wave_bg": "#0a180c",
    },
}

DEFAULT_THEME     = "dark"
DEFAULT_LIKED     = "❤ Понравившиеся"
DEFAULT_PLAYLIST  = "Мой плейлист"
BG_DARKEN         = 0.45
COVER_SIZE        = 150
COVER_RADIUS      = 16
CONTENT_MAX_WIDTH = 1400
VOLUME_MAX_WIDTH  = 180
HISTORY_LIMIT     = 50000

G_PLAY        = "▶"
G_PAUSE       = "❚❚"
G_STOP        = "■"
G_PREV        = "◀◀"
G_NEXT        = "▶▶"
G_HEART       = "♥"
G_HEART_EMPTY = "♡"

JAMENDO_URL = "https://api.jamendo.com/v3.0/tracks/"
JAMENDO_KEY_URL = "https://devportal.jamendo.com/"
ITUNES_URL = "https://itunes.apple.com/search"


GENRE_BPM = {
    "ambient": 70, "classical": 80, "piano": 75, "lofi": 80,
    "jazz": 100, "blues": 90, "folk": 90, "country": 95,
    "reggae": 75, "soul": 90, "funk": 105,
    "pop": 120, "rock": 125, "indie": 120, "punk": 160,
    "metal": 160, "hardcore": 170,
    "electronic": 128, "electro": 128, "house": 124,
    "techno": 135, "trance": 138, "dubstep": 140,
    "drum and bass": 174, "dnb": 174,
    "hip-hop": 90, "hiphop": 90, "rap": 95, "trap": 130,
    "r&b": 95, "rnb": 95, "dance": 128, "edm": 128,
}

GENRE_ENERGY = {
    "ambient": 0.10, "classical": 0.20, "piano": 0.22,
    "lofi": 0.25, "folk": 0.30, "blues": 0.35, "jazz": 0.35,
    "country": 0.40, "soul": 0.45, "reggae": 0.45,
    "pop": 0.65, "indie": 0.60, "hip-hop": 0.60, "rap": 0.65,
    "rnb": 0.60, "rock": 0.75, "funk": 0.70,
    "electronic": 0.75, "electro": 0.75, "house": 0.70,
    "dance": 0.80, "trance": 0.80, "techno": 0.85,
    "dubstep": 0.90, "metal": 0.95, "hardcore": 0.98,
    "punk": 0.90, "drum and bass": 0.92, "dnb": 0.92,
}


FAQ_HTML = """
<h2>❓ Часто задаваемые вопросы</h2>
<h3>🎵 Как добавить музыку?</h3>
<p>Кнопки <b>＋ Файлы</b> и <b>📁 Папка</b> внизу приложения.</p>

<h3>💓 Что такое «живой пульс»?</h3>
<p>Визуализатор реагирует на <b>реальный бит</b> вашего трека.
Требуется PySide6 6.8+ (для получения аудио-буферов).
Для лучшей точности: <code>pip install numpy</code>.
Отключается в ⚙ Настройках.</p>

<h3>🎯 Что такое «Похожие»?</h3>
<p>Анализ трека по 6 параметрам: BPM, тональность, энергия,
текстура, год, жанр. По этим характеристикам ищутся похожие
по звучанию треки в вашей библиотеке. Кнопка <b>🎯 Похожие</b>
рядом с обложкой или ПКМ по треку.</p>

<h3>🌊 Что такое «Волна»?</h3>
<p>Вкладка с онлайн-рекомендациями. Три режима, два источника
(iTunes / Jamendo). Стримы можно слушать прямо в плеере.</p>

<h3>📊 Отчёты и вкладка «Из Волны»</h3>
<p>В 📊 Отчётах есть режим <b>🌊 Из Волны</b> — показывает статистику
только по стримам из «Волны»: время, количество, исполнителей,
разных треков. Обычные режимы (День/Неделя/Месяц) считают
только локальные файлы.</p>

<h3>💾 Где хранятся настройки?</h3>
<p><code>%USERPROFILE%\\.music_player\\config.json</code>.</p>
"""


# ==================================================================
#  Анализатор: BEAT DETECTION + 3 агрегата
# ==================================================================

class AudioSpectrumAnalyzer(QObject):
    audio_stats_ready = Signal(float, float, float, bool, float)

    def __init__(self, player, parent=None):
        super().__init__(parent)
        self.player = player
        self._available = False
        self._buffer_output = None
        self._enabled = True
        self._using_numpy = False
        self._last_process = 0.0
        self._min_interval = 0.033

        self._max_bass = 0.01
        self._max_mid = 0.01
        self._max_high = 0.01

        self._bass_avg = 0.0
        self._beat_cooldown = 0.22
        self._last_beat_time = 0.0
        self._warmup = 0

        try:
            import numpy  # noqa: F401
            self._using_numpy = True
        except ImportError:
            pass

        try:
            from PySide6.QtMultimedia import QAudioBufferOutput
            self._buffer_output = QAudioBufferOutput(self)
            self._buffer_output.audioBufferReceived.connect(self._on_buffer)
            player.setAudioBufferOutput(self._buffer_output)
            self._available = True
        except (ImportError, AttributeError, RuntimeError):
            self._available = False

    def is_available(self):
        return self._available

    def using_numpy(self):
        return self._using_numpy

    def set_enabled(self, enabled):
        self._enabled = bool(enabled) and self._available
        if not enabled:
            self._reset()

    def _reset(self):
        self._max_bass = 0.01
        self._max_mid = 0.01
        self._max_high = 0.01
        self._bass_avg = 0.0
        self._warmup = 0

    def reset(self):
        self._reset()

    def _on_buffer(self, buffer):
        if not self._enabled or not self._available:
            return
        try:
            if self.player.playbackState() != QMediaPlayer.PlayingState:
                return
        except Exception:
            pass
        now = time.time()
        if now - self._last_process < self._min_interval:
            return
        self._last_process = now
        try:
            feats = self._compute_features(buffer)
            if feats is None:
                return
            bass_raw, mid_raw, high_raw, amp_raw = feats

            self._max_bass = max(bass_raw, self._max_bass * 0.998, 0.005)
            self._max_mid  = max(mid_raw,  self._max_mid  * 0.998, 0.005)
            self._max_high = max(high_raw, self._max_high * 0.998, 0.003)

            bass_norm = min(1.0, bass_raw / self._max_bass)
            mid_norm  = min(1.0, mid_raw  / self._max_mid)
            high_norm = min(1.0, high_raw / self._max_high)
            amp_norm  = min(1.0, amp_raw * 4.0)

            beat = self._detect_beat(bass_raw, now)
            self.audio_stats_ready.emit(
                bass_norm, mid_norm, high_norm, beat, amp_norm)
        except Exception:
            pass

    def _detect_beat(self, bass_energy, now):
        self._bass_avg = self._bass_avg * 0.90 + bass_energy * 0.10
        self._warmup += 1
        if self._warmup < 8:
            return False
        if now - self._last_beat_time < self._beat_cooldown:
            return False
        if self._bass_avg < 0.001:
            return False
        if bass_energy > self._bass_avg * 1.5:
            self._last_beat_time = now
            self._warmup = max(4, self._warmup // 2)
            return True
        return False

    def _compute_features(self, buffer):
        from PySide6.QtMultimedia import QAudioFormat
        fmt = buffer.format()
        sample_format = fmt.sampleFormat()
        n_channels = fmt.channelCount()
        sample_rate = fmt.sampleRate()
        n_frames = buffer.frameCount()
        if n_frames < 64 or n_channels < 1 or sample_rate <= 0:
            return None
        data = buffer.constData()
        if isinstance(data, memoryview):
            raw_bytes = data.tobytes()
        else:
            raw_bytes = bytes(data)
        import array
        try:
            if sample_format == QAudioFormat.SampleFormat.Float:
                raw = array.array('f', raw_bytes)
            elif sample_format == QAudioFormat.SampleFormat.Int16:
                raw = array.array('h', raw_bytes)
                raw = [x / 32768.0 for x in raw]
            elif sample_format == QAudioFormat.SampleFormat.Int32:
                raw = array.array('i', raw_bytes)
                raw = [x / 2147483648.0 for x in raw]
            elif sample_format == QAudioFormat.SampleFormat.UInt8:
                raw = array.array('B', raw_bytes)
                raw = [(x - 128) / 128.0 for x in raw]
            else:
                return None
        except Exception:
            return None
        if n_channels > 1:
            n = len(raw) // n_channels
            mono = [0.0] * n
            for i in range(n):
                s = 0.0
                for c in range(n_channels):
                    s += raw[i * n_channels + c]
                mono[i] = s / n_channels
        else:
            mono = list(raw)
        N = 512 if self._using_numpy else 256
        if len(mono) < N:
            return None
        samples = mono[-N:]
        amp = math.sqrt(sum(s * s for s in samples) / len(samples))
        windowed = [0.0] * N
        for i in range(N):
            windowed[i] = samples[i] * 0.5 * (1.0 - math.cos(2.0 * math.pi * i / (N - 1)))
        mags = self._fft_magnitudes(windowed)
        if mags is None:
            return None
        bin_width = sample_rate / N
        nb = len(mags)

        def band_energy(low_hz, high_hz):
            b0 = max(1, int(low_hz / bin_width))
            b1 = min(nb, int(high_hz / bin_width))
            if b1 <= b0:
                return 0.0
            return sum(mags[b0:b1]) / (b1 - b0)

        bass = band_energy(30.0, 150.0)
        mid = band_energy(300.0, 3000.0)
        high = band_energy(4000.0, 10000.0)
        return (bass, mid, high, amp)

    def _fft_magnitudes(self, samples):
        N = len(samples)
        if self._using_numpy:
            try:
                import numpy as np
                arr = np.array(samples, dtype=np.float64)
                res = np.fft.rfft(arr)
                mags = np.abs(res) / (N / 2)
                return [float(m) for m in mags]
            except Exception:
                pass
        if N & (N - 1) != 0:
            return None
        c = [complex(s, 0) for s in samples]
        j = 0
        for i in range(1, N):
            bit = N >> 1
            while j & bit:
                j ^= bit
                bit >>= 1
            j ^= bit
            if i < j:
                c[i], c[j] = c[j], c[i]
        length = 2
        while length <= N:
            angle = -2.0 * math.pi / length
            wlen = complex(math.cos(angle), math.sin(angle))
            half = length // 2
            for i in range(0, N, length):
                w = complex(1.0, 0.0)
                for k in range(half):
                    u = c[i + k]
                    v = c[i + k + half] * w
                    c[i + k] = u + v
                    c[i + k + half] = u - v
                    w *= wlen
            length <<= 1
        return [abs(c[i]) / (N / 2) for i in range(N // 2)]


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
#  Визуализация — ПУЛЬС НА БИТ
# ==================================================================

class WaveWidget(QWidget):
    def __init__(self, accent, bg, parent=None):
        super().__init__(parent)
        self.accent = QColor(accent) if not isinstance(accent, QColor) else accent
        if isinstance(bg, (tuple, list)) and len(bg) >= 3:
            self.bg = QColor(int(bg[0]), int(bg[1]), int(bg[2]))
        elif isinstance(bg, QColor):
            self.bg = bg
        else:
            self.bg = QColor(bg)

        self.live_enabled = True
        self.live_capable = False
        self.live_active = False
        self._demo_blend = 1.0

        self.bass_env = 0.0
        self.mid_env = 0.0
        self.high_env = 0.0
        self.amp_env = 0.0

        self.beat_pulse = 0.0
        self.ripples = []
        self.burst_particles = []

        self.phase = 0.0
        self._pulse = 0.0

        self.particles = []
        self.stars = []
        self.comets = []
        self._cache_size = None
        self._comet_spawn = 0
        self._last_stats_time = 0.0

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._timer.setInterval(33)
        self.setMinimumHeight(260)
        self.setMaximumHeight(300)

    def set_colors(self, accent, bg):
        self.accent = QColor(accent)
        if isinstance(bg, (tuple, list)) and len(bg) >= 3:
            self.bg = QColor(int(bg[0]), int(bg[1]), int(bg[2]))
        else:
            self.bg = QColor(bg)
        self.update()

    def set_live_enabled(self, enabled):
        self.live_enabled = bool(enabled)
        self.update()

    def set_live_capable(self, capable):
        self.live_capable = bool(capable)

    def set_beat_stats(self, bass, mid, high, beat, amp):
        if not self.live_enabled:
            return
        self.live_active = True
        self._last_stats_time = time.time()

        if bass > self.bass_env:
            self.bass_env = bass
        else:
            self.bass_env = self.bass_env * 0.82 + bass * 0.18

        if mid > self.mid_env:
            self.mid_env = mid
        else:
            self.mid_env = self.mid_env * 0.80 + mid * 0.20

        if high > self.high_env:
            self.high_env = high
        else:
            self.high_env = self.high_env * 0.78 + high * 0.22

        if amp > self.amp_env:
            self.amp_env = amp
        else:
            self.amp_env = self.amp_env * 0.90 + amp * 0.10

        if beat:
            self._trigger_beat()
        self.update()

    def set_silence(self):
        self._last_stats_time = 0.0

    def _trigger_beat(self):
        self.beat_pulse = 1.0
        self.ripples.append({
            "r": 20.0, "max_r": 220.0, "alpha": 0.85,
            "life": 0.0, "max_life": 0.85,
        })
        cx, cy = self.width() / 2.0, self.height() / 2.0
        count = 10 + int(self.bass_env * 8)
        for _ in range(count):
            ang = random.uniform(0, 2 * math.pi)
            speed = random.uniform(90, 260)
            self.burst_particles.append({
                "x": cx, "y": cy,
                "vx": math.cos(ang) * speed,
                "vy": math.sin(ang) * speed,
                "life": 0.0,
                "max_life": random.uniform(0.35, 0.85),
                "size": random.uniform(1.5, 3.2),
            })

    def showEvent(self, e):
        self._timer.start(); super().showEvent(e)

    def hideEvent(self, e):
        self._timer.stop(); super().hideEvent(e)

    def _ensure_particles(self):
        size = (self.width(), self.height())
        if self._cache_size != size or not self.particles:
            self._cache_size = size
            w, h = size
            self.particles = [
                [random.uniform(0, w), random.uniform(0, h),
                 random.uniform(0.3, 1.3), random.uniform(1.2, 3.2),
                 random.uniform(0.15, 0.85), random.uniform(-0.20, 0.20)]
                for _ in range(40)
            ]
            self.stars = [
                [random.uniform(0, w), random.uniform(0, h * 0.35),
                 random.uniform(0.6, 1.8), random.uniform(0.4, 1.0),
                 random.uniform(0.5, 2.0)]
                for _ in range(22)
            ]
            self.comets = []

    def _tick(self):
        now = time.time()
        self._ensure_particles()
        h, w = self.height(), self.width()
        dt = 0.033

        if now - self._last_stats_time > 0.15:
            self.bass_env *= 0.94
            self.mid_env *= 0.94
            self.high_env *= 0.94
            self.amp_env *= 0.94
            if self.bass_env < 0.001: self.bass_env = 0.0
            if self.mid_env < 0.001: self.mid_env = 0.0
            if self.high_env < 0.001: self.high_env = 0.0
            if self.amp_env < 0.001: self.amp_env = 0.0

        has_live = (self.live_enabled and self.live_capable
                    and (self.bass_env + self.mid_env + self.high_env) > 0.008)
        target_blend = 0.0 if has_live else 1.0

        self._demo_blend += (target_blend - self._demo_blend) * 0.08
        if abs(self._demo_blend - target_blend) < 0.005:
            self._demo_blend = target_blend

        self.beat_pulse *= 0.86
        if self.beat_pulse < 0.01:
            self.beat_pulse = 0.0

        alive_ripples = []
        for r in self.ripples:
            r["life"] += dt
            p = min(1.0, r["life"] / r["max_life"])
            r["r"] = 20.0 + (r["max_r"] - 20.0) * p
            r["alpha"] = 0.85 * (1.0 - p)
            if r["alpha"] > 0.02:
                alive_ripples.append(r)
        self.ripples = alive_ripples

        alive_burst = []
        for bp in self.burst_particles:
            bp["life"] += dt
            if bp["life"] >= bp["max_life"]:
                continue
            bp["x"] += bp["vx"] * dt
            bp["y"] += bp["vy"] * dt
            bp["vx"] *= 0.93
            bp["vy"] *= 0.93
            alive_burst.append(bp)
        self.burst_particles = alive_burst

        live_rate = 0.012 + self.mid_env * 0.09
        demo_rate = 0.045
        rate = live_rate * (1.0 - self._demo_blend) + demo_rate * self._demo_blend
        self.phase += rate
        if self.phase > 1000:
            self.phase = 0
        self._pulse = (self._pulse + 0.07) % (2 * math.pi)

        for s in self.stars:
            s[3] += 0.02 * s[4]
            if s[3] > 1.0:
                s[3] = 1.0 - (s[3] - 1.0); s[4] = -abs(s[4])
            elif s[3] < 0.2:
                s[3] = 0.2 + (0.2 - s[3]); s[4] = abs(s[4])

        speed_mult = 0.5 + self.amp_env * 1.5
        for p in self.particles:
            p[1] -= p[2] * speed_mult
            p[0] += p[5]
            if p[1] < -5:
                p[1] = h + 5
                p[0] = random.uniform(0, w)
            if p[0] < -5:
                p[0] = w + 5
            elif p[0] > w + 5:
                p[0] = -5

        if self._demo_blend < 0.5:
            spawn_chance = 0.005 + self.high_env * 0.02
            if random.random() < spawn_chance and len(self.comets) < 2:
                self.comets.append({
                    "x": random.uniform(0, w * 0.6),
                    "y": random.uniform(0, 25),
                    "vx": random.uniform(4, 8), "vy": random.uniform(1.5, 3),
                    "life": 0, "max_life": random.randint(25, 45),
                    "size": random.uniform(1.5, 2.5),
                })
        else:
            self._comet_spawn = (self._comet_spawn + 1) % 120
            if self._comet_spawn == 0 and len(self.comets) < 2:
                self.comets.append({
                    "x": random.uniform(0, w * 0.6),
                    "y": random.uniform(0, 30),
                    "vx": random.uniform(4, 8), "vy": random.uniform(1.5, 3),
                    "life": 0, "max_life": random.randint(25, 45),
                    "size": random.uniform(1.5, 2.5),
                })

        new_comets = []
        for c in self.comets:
            c["x"] += c["vx"]; c["y"] += c["vy"]; c["life"] += 1
            if c["life"] < c["max_life"] and c["x"] < w + 50 and c["y"] < h:
                new_comets.append(c)
        self.comets = new_comets

        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()

        top = QColor(self.bg).lighter(120)
        bottom = QColor(self.bg).darker(170)
        grad = QLinearGradient(0, 0, 0, h)
        grad.setColorAt(0, top); grad.setColorAt(1, bottom)
        p.fillRect(0, 0, w, h, grad)

        for (sx, sy, ssize, salpha, speed) in self.stars:
            c = QColor(255, 255, 255); c.setAlpha(int(salpha * 200))
            p.setBrush(c); p.setPen(Qt.NoPen)
            p.drawEllipse(QPoint(int(sx), int(sy)), int(ssize), int(ssize))

        live_alpha = 1.0 - self._demo_blend
        demo_alpha = self._demo_blend
        if live_alpha > 0.005:
            self._paint_live(p, w, h, live_alpha)
        if demo_alpha > 0.005:
            self._paint_demo(p, w, h, demo_alpha)

        for (px, py, speed, size, alpha, drift) in self.particles:
            c = QColor(self.accent).lighter(130)
            c.setAlpha(int(alpha * 255 * 0.7))
            p.setBrush(c); p.setPen(Qt.NoPen)
            p.drawEllipse(QPoint(int(px), int(py)), int(size), int(size))

        for c in self.comets:
            x, y = c["x"], c["y"]
            vx, vy = c["vx"], c["vy"]
            life_pct = c["life"] / c["max_life"]
            alpha = int((1.0 - life_pct) * 220)
            for k in range(6):
                t = k / 6
                hx = int(x - vx * t * 2.5)
                hy = int(y - vy * t * 2.5)
                tail_alpha = int(alpha * (1.0 - t) * 0.55)
                tc = QColor(self.accent).lighter(150); tc.setAlpha(tail_alpha)
                p.setBrush(tc); p.setPen(Qt.NoPen)
                p.drawEllipse(QPoint(hx, hy),
                              max(1, int(c["size"] * (1.0 - t))),
                              max(1, int(c["size"] * (1.0 - t))))
            hc = QColor(255, 255, 255); hc.setAlpha(alpha)
            p.setBrush(hc); p.setPen(Qt.NoPen)
            p.drawEllipse(QPoint(int(x), int(y)), int(c["size"]), int(c["size"]))

        glow = QLinearGradient(0, 0, 0, 55)
        c_top = QColor(self.accent); c_top.setAlpha(85)
        c_mid = QColor(self.accent); c_mid.setAlpha(0)
        glow.setColorAt(0, c_top); glow.setColorAt(1, c_mid)
        p.fillRect(0, 0, w, 55, glow)

        p.setPen(QColor(255, 255, 255, 245))
        f = QFont("Segoe UI", 16); f.setBold(True); p.setFont(f)
        p.drawText(self.rect().adjusted(0, 15, 0, 0),
                   Qt.AlignHCenter | Qt.AlignTop, "🌊  Твоя волна")

        p.setFont(QFont("Segoe UI", 8, QFont.Bold))
        if self._demo_blend < 0.5:
            if self.live_enabled and self.live_capable and self.amp_env > 0.01:
                alpha = int(120 + self.beat_pulse * 130)
                p.setPen(QColor(255, 90, 90, alpha))
                p.drawText(self.rect().adjusted(0, 16, -12, 0),
                           Qt.AlignRight | Qt.AlignTop, "● BEAT")
            elif self.live_enabled and self.live_capable:
                p.setPen(QColor(210, 210, 210, 180))
                p.drawText(self.rect().adjusted(0, 16, -12, 0),
                           Qt.AlignRight | Qt.AlignTop, "○ LISTENING")
            else:
                p.setPen(QColor(150, 150, 150, 160))
                p.drawText(self.rect().adjusted(0, 16, -12, 0),
                           Qt.AlignRight | Qt.AlignTop, "○ DEMO")
        else:
            if self.live_enabled and self.live_capable:
                p.setPen(QColor(180, 180, 180, 180))
                p.drawText(self.rect().adjusted(0, 16, -12, 0),
                           Qt.AlignRight | Qt.AlignTop, "○ IDLE")
            else:
                p.setPen(QColor(150, 150, 150, 160))
                p.drawText(self.rect().adjusted(0, 16, -12, 0),
                           Qt.AlignRight | Qt.AlignTop, "○ DEMO")

        p.end()

    def _paint_live(self, p, w, h, alpha_scale):
        cx, cy = w / 2.0, h / 2.0

        base_r = 40 + self.bass_env * 30
        beat_r = self.beat_pulse * 100
        pulse_r = base_r + beat_r

        rg = QRadialGradient(cx, cy, max(pulse_r * 2.2, 60))
        intensity = int((60 + self.beat_pulse * 130) * alpha_scale)
        c1 = QColor(self.accent); c1.setAlpha(intensity)
        c2 = QColor(self.accent); c2.setAlpha(0)
        rg.setColorAt(0, c1); rg.setColorAt(1, c2)
        p.setBrush(rg); p.setPen(Qt.NoPen)
        p.drawEllipse(QPoint(int(cx), int(cy)),
                      int(pulse_r * 2.2), int(pulse_r * 2.2))

        if self.beat_pulse > 0.05:
            core_r = 8 + self.beat_pulse * 30
            core = QColor(255, 255, 255)
            core.setAlpha(int(self.beat_pulse * 220 * alpha_scale))
            p.setBrush(core); p.setPen(Qt.NoPen)
            p.drawEllipse(QPoint(int(cx), int(cy)), int(core_r), int(core_r))

        for r in self.ripples:
            c = QColor(self.accent).lighter(150)
            c.setAlpha(int(r["alpha"] * 230 * alpha_scale))
            p.setPen(QPen(c, 2.0))
            p.setBrush(Qt.NoBrush)
            p.drawEllipse(QPoint(int(cx), int(cy)), int(r["r"]), int(r["r"]))

        wave_amp = 5 + self.mid_env * 28 + self.beat_pulse * 22
        for layer in range(6):
            path = QPainterPath()
            layer_phase = self.phase + layer * 0.75
            amp = wave_amp * (0.7 + layer * 0.18)
            freq = 0.017 - layer * 0.0018
            y_base = h * 0.44 + layer * 9
            path.moveTo(0, h)
            x = 0
            while x <= w + 10:
                y = (y_base
                     + math.sin(x * freq + layer_phase) * amp
                     + math.sin(x * freq * 2.1 + layer_phase * 1.3) * amp * 0.32
                     + math.sin(x * freq * 0.55 + layer_phase * 0.7) * amp * 0.28)
                path.lineTo(x, y)
                x += 8
            path.lineTo(w, h)
            path.closeSubpath()
            col = QColor(self.accent)
            alpha = 15 + layer * 13 + int(self.mid_env * 55) + int(self.beat_pulse * 40)
            col.setAlpha(min(255, int(alpha * alpha_scale)))
            p.setBrush(col); p.setPen(Qt.NoPen)
            p.drawPath(path)

        for bp in self.burst_particles:
            life_pct = bp["life"] / bp["max_life"]
            alpha = int((1.0 - life_pct) * 255 * alpha_scale)
            c = QColor(self.accent).lighter(160)
            c.setAlpha(alpha)
            p.setBrush(c); p.setPen(Qt.NoPen)
            size = bp["size"] * (1.0 - life_pct * 0.5)
            p.drawEllipse(QPoint(int(bp["x"]), int(bp["y"])),
                          max(1, int(size)), max(1, int(size)))

    def _paint_demo(self, p, w, h, alpha_scale):
        cx, cy = w / 2.0, h / 2.0
        pulse_r = 45 + 18 * (0.5 + 0.5 * math.sin(self._pulse))
        rg = QRadialGradient(cx, cy, pulse_r * 2.5)
        c1 = QColor(self.accent); c1.setAlpha(int(65 * alpha_scale))
        c2 = QColor(self.accent); c2.setAlpha(0)
        rg.setColorAt(0, c1); rg.setColorAt(1, c2)
        p.setBrush(rg); p.setPen(Qt.NoPen)
        p.drawEllipse(QPoint(int(cx), int(cy)),
                      int(pulse_r * 2.5), int(pulse_r * 2.5))

        for layer in range(7):
            path = QPainterPath()
            phase = self.phase + layer * 0.85
            amp = 6 + layer * 6
            freq = 0.020 - layer * 0.0020
            y_base = h * 0.42 + layer * 10
            path.moveTo(0, h)
            x = 0
            while x <= w + 10:
                y = (y_base
                     + math.sin(x * freq + phase) * amp
                     + math.sin(x * freq * 2.3 + phase * 1.4) * amp * 0.35
                     + math.sin(x * freq * 0.7 + phase * 0.5) * amp * 0.22)
                path.lineTo(x, y)
                x += 8
            path.lineTo(w, h)
            path.closeSubpath()
            col = QColor(self.accent)
            col.setAlpha(int((24 + layer * 16) * alpha_scale))
            p.setBrush(col); p.setPen(Qt.NoPen)
            p.drawPath(path)


# ==================================================================
#  Диаграммы (Отчёты)
# ==================================================================

class PieChartWidget(QWidget):
    def __init__(self, title, text_color, palette, parent=None):
        super().__init__(parent)
        self.title = title
        self.text_color = text_color
        self.palette = palette
        self.entries = []
        self.setMinimumHeight(280)

    def set_title(self, title):
        self.title = title
        self.update()

    def set_data(self, entries):
        self.entries = entries; self.update()

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
        self.setMinimumHeight(140)

    def set_title(self, title):
        self.title = title
        self.update()

    def set_data(self, values, labels, highlight=-1):
        self.values = values; self.labels = labels
        self.highlight = highlight; self.update()

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

        chart_top = 26; chart_bottom = h - 22
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
            p.setBrush(color); p.setPen(Qt.NoPen)
            if bh > 2:
                p.drawRoundedRect(x, chart_bottom - bh, bar_w, bh, 3, 3)
            else:
                p.setBrush(QColor(self.text_color))
                p.drawRoundedRect(x, chart_bottom - 1, bar_w, 2, 1, 1)
            p.setPen(QColor(self.text_color))
            p.drawText(x - 6, chart_bottom + 2, bar_w + 12, 16,
                       Qt.AlignHCenter | Qt.AlignTop, label)


# ==================================================================
#  Радар-чарт характеристик
# ==================================================================

class RadarChartWidget(QWidget):
    AXES = ("BPM", "Key", "Energy", "Texture", "Year", "Genre")

    def __init__(self, size=120, show_labels=True, parent=None):
        super().__init__(parent)
        self.setFixedSize(size, size)
        self.values = [0.0] * 6
        self.labels = list(self.AXES)
        self.show_labels = show_labels
        self.accent = QColor("#7c5cff")
        self.text_color = QColor("#f0f0f5")
        self.grid_color = QColor(255, 255, 255, 45)
        self.margin = 16 if show_labels else 4

    def set_colors(self, accent, text, grid=None):
        self.accent = QColor(accent)
        self.text_color = QColor(text)
        if grid is not None:
            self.grid_color = QColor(grid)
        self.update()

    def set_values(self, values):
        self.values = [max(0.0, min(1.0, float(v))) for v in values]
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()
        cx, cy = w / 2.0, h / 2.0
        r = min(w, h) / 2.0 - self.margin
        n = 6
        if r <= 2:
            p.end(); return

        for level in (0.25, 0.5, 0.75, 1.0):
            poly = QPolygonF()
            for i in range(n):
                ang = -math.pi / 2 + i * 2 * math.pi / n
                poly.append(QPointF(cx + math.cos(ang) * r * level,
                                    cy + math.sin(ang) * r * level))
            p.setPen(QPen(self.grid_color, 0.8))
            p.setBrush(Qt.NoBrush)
            p.drawPolygon(poly)

        for i in range(n):
            ang = -math.pi / 2 + i * 2 * math.pi / n
            p.setPen(QPen(self.grid_color, 0.8))
            p.drawLine(QPointF(cx, cy),
                       QPointF(cx + math.cos(ang) * r,
                               cy + math.sin(ang) * r))

        poly = QPolygonF()
        pts = []
        for i, v in enumerate(self.values):
            ang = -math.pi / 2 + i * 2 * math.pi / n
            x = cx + math.cos(ang) * r * v
            y = cy + math.sin(ang) * r * v
            poly.append(QPointF(x, y))
            pts.append((x, y))
        fill = QColor(self.accent); fill.setAlpha(110)
        p.setBrush(fill)
        p.setPen(QPen(self.accent, 1.6))
        p.drawPolygon(poly)

        p.setBrush(self.accent); p.setPen(Qt.NoPen)
        dot = 3 if self.show_labels else 2
        for x, y in pts:
            p.drawEllipse(QPointF(x, y), dot, dot)

        if self.show_labels:
            p.setFont(QFont("Segoe UI", 6, QFont.Bold))
            p.setPen(self.text_color)
            for i, label in enumerate(self.labels):
                ang = -math.pi / 2 + i * 2 * math.pi / n
                lx = cx + math.cos(ang) * (r + 10)
                ly = cy + math.sin(ang) * (r + 10)
                rect = QRect(int(lx - 22), int(ly - 7), 44, 14)
                p.drawText(rect, Qt.AlignCenter, label)

        p.end()


# ==================================================================
#  Диалоги
# ==================================================================

class TrackInfoDialog(QDialog):
    def __init__(self, parent, name, artist, genre=""):
        super().__init__(parent)
        self.setWindowTitle("Информация о треке")
        self.setStyleSheet(parent.styleSheet())
        self.setMinimumWidth(400)
        form = QFormLayout(self)
        self.name_edit = QLineEdit(name)
        self.name_edit.setPlaceholderText("Отображаемое название")
        form.addRow("Название:", self.name_edit)
        self.artist_edit = QLineEdit(artist)
        self.artist_edit.setPlaceholderText("Исполнитель")
        form.addRow("Исполнитель:", self.artist_edit)
        self.genre_edit = QLineEdit(genre)
        self.genre_edit.setPlaceholderText("Rock, Jazz, Electronic…")
        form.addRow("Жанр:", self.genre_edit)
        btns = QHBoxLayout()
        cancel = QPushButton("Отмена"); cancel.clicked.connect(self.reject)
        ok = QPushButton("Сохранить"); ok.clicked.connect(self.accept)
        ok.setDefault(True)
        btns.addStretch(); btns.addWidget(cancel); btns.addWidget(ok)
        form.addRow(btns)

    def values(self):
        return (self.name_edit.text().strip(),
                self.artist_edit.text().strip(),
                self.genre_edit.text().strip())


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
            f"QTextBrowser {{ background: rgba({r},{g},{b},230);"
            f" color: {t['text']}; border: 1px solid rgba(255,255,255,20);"
            f" border-radius: 12px; padding: 12px; }}")
        layout.addWidget(browser)
        ok_btn = QPushButton("Понятно")
        ok_btn.clicked.connect(self.accept)
        ok_btn.setDefault(True)
        layout.addWidget(ok_btn)


# ==================================================================
#  Диалог «Похожие треки»
# ==================================================================

class SimilarTracksDialog(QDialog):
    def __init__(self, player, source_path):
        super().__init__(player)
        self.player = player
        self.source_path = source_path
        self.setWindowTitle("🎯 Похожие треки")
        self.setStyleSheet(player.styleSheet())
        self.resize(820, 760)
        self.setMinimumWidth(700)

        t = player.theme()
        main = QVBoxLayout(self)
        main.setContentsMargins(16, 16, 16, 16)
        main.setSpacing(12)

        header_card = QFrame(); header_card.setObjectName("glassPanel")
        hl = QHBoxLayout(header_card)
        hl.setContentsMargins(18, 16, 18, 16)
        hl.setSpacing(18)

        self.radar = RadarChartWidget(size=180, show_labels=True, parent=self)
        self.radar.set_colors(t["accent"], t["text"])
        hl.addWidget(self.radar, 0, Qt.AlignTop)

        info_col = QVBoxLayout(); info_col.setSpacing(4)
        self.title_lbl = QLabel()
        f = self.title_lbl.font(); f.setPointSize(15); f.setBold(True)
        self.title_lbl.setFont(f); self.title_lbl.setWordWrap(True)
        info_col.addWidget(self.title_lbl)

        self.artist_lbl = QLabel()
        self.artist_lbl.setObjectName("dim")
        info_col.addWidget(self.artist_lbl)

        info_col.addSpacing(8)
        self.dna_lbl = QLabel()
        self.dna_lbl.setWordWrap(True)
        self.dna_lbl.setStyleSheet(
            f"color: {t['text_dim']}; font-size: 11px; line-height: 1.6;")
        info_col.addWidget(self.dna_lbl)
        info_col.addStretch()

        actions = QHBoxLayout(); actions.setSpacing(6)
        self.play_btn = QPushButton("▶  Играть")
        self.play_btn.clicked.connect(self._play_source)
        actions.addWidget(self.play_btn)

        self.wave_btn = QPushButton("🌊  В «Волну»")
        self.wave_btn.setObjectName("secondary")
        self.wave_btn.clicked.connect(self._open_source_in_wave)
        if not player.internet_enabled:
            self.wave_btn.setEnabled(False)
        actions.addWidget(self.wave_btn)
        actions.addStretch()
        info_col.addLayout(actions)

        hl.addLayout(info_col, 1)
        main.addWidget(header_card)

        self.section_lbl = QLabel("🎯  Похожие в вашей библиотеке")
        fh = self.section_lbl.font(); fh.setPointSize(12); fh.setBold(True)
        self.section_lbl.setFont(fh)
        main.addWidget(self.section_lbl)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.NoFrame)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.host = QWidget()
        self.host_l = QVBoxLayout(self.host)
        self.host_l.setContentsMargins(0, 0, 0, 0)
        self.host_l.setSpacing(4)
        self.scroll.setWidget(self.host)
        main.addWidget(self.scroll, 1)

        bottom = QHBoxLayout()
        self.rescan_btn = QPushButton("↻  Пересчитать")
        self.rescan_btn.setObjectName("secondary")
        self.rescan_btn.setToolTip("Сбросить кэш и заново проанализировать")
        self.rescan_btn.clicked.connect(self._rescan)
        bottom.addWidget(self.rescan_btn)
        bottom.addStretch()
        close_btn = QPushButton("Закрыть")
        close_btn.clicked.connect(self.accept)
        close_btn.setDefault(True)
        bottom.addWidget(close_btn)
        main.addLayout(bottom)

        self._load()
        QTimer.singleShot(40, self._populate_similar)

    def _load(self):
        path = self.source_path
        self.title_lbl.setText(self.player._display_name(path))
        self.artist_lbl.setText(self.player._display_artist(path) or "—")

        try:
            dna = self.player._track_dna(path)
        except Exception:
            dna = None

        if not dna:
            self.radar.set_values([0.0] * 6)
            self.dna_lbl.setText("⚠  Не удалось проанализировать трек")
            return

        self.radar.set_values(dna["normalized"])
        r = dna["raw"]
        length_sec = int(r["length"])
        length_str = (f"{length_sec // 60}:{length_sec % 60:02d}"
                      if length_sec > 0 else "—")
        audio_note = "" if r.get("has_audio") else "  <i>(только теги)</i>"

        lines = [
            f"🎚  BPM: <b>{r['bpm']:.0f}</b>",
            f"🎼  Key: <b>{r['key_str'] or '—'}</b>",
            f"⚡  Energy: <b>{r['energy'] * 100:.0f}%</b>{audio_note}",
            f"🧵  Texture: <b>{r['zcr'] * 100:.0f}%</b>",
            f"⏱  Length: <b>{length_str}</b>",
            f"📅  Year: <b>{r['year'] or '—'}</b>",
            f"🎵  Genre: <b>{r['genre'] or '—'}</b>",
        ]
        self.dna_lbl.setText("<br>".join(lines))

    def _populate_similar(self):
        while self.host_l.count() > 0:
            item = self.host_l.takeAt(0)
            w = item.widget()
            if w: w.deleteLater()

        similar = self.player._find_similar_local(self.source_path, limit=25)

        if not similar:
            empty = QLabel(
                "Похожих треков не нашлось.\n\n"
                "Добавьте больше музыки в библиотеку.")
            empty.setObjectName("dim")
            empty.setWordWrap(True)
            empty.setAlignment(Qt.AlignCenter)
            self.host_l.addWidget(empty)
            self.host_l.addStretch()
            return

        self.section_lbl.setText(
            f"🎯  Похожие в вашей библиотеке — найдено {len(similar)}")

        for path, dist, pct in similar:
            self.host_l.addWidget(self._make_similar_row(path, dist, pct))
        self.host_l.addStretch()

    def _make_similar_row(self, path, dist, pct):
        t = self.player.theme()
        card = QFrame(); card.setObjectName("glassPanel")
        row = QHBoxLayout(card)
        row.setContentsMargins(10, 8, 10, 8)
        row.setSpacing(10)

        radar = RadarChartWidget(size=64, show_labels=False, parent=card)
        radar.set_colors(t["accent"], t["text"], "rgba(255,255,255,40)")
        try:
            dna = self.player._track_dna(path)
            radar.set_values(dna["normalized"])
            r = dna["raw"]
            bpm_s = f"{r['bpm']:.0f} BPM"
            genre_s = r["genre"] or "—"
            summary = f"{bpm_s}  ·  {genre_s}"
        except Exception:
            radar.set_values([0.0] * 6)
            summary = ""
        row.addWidget(radar)

        info = QVBoxLayout(); info.setSpacing(2)
        name_lbl = QLabel(self.player._display_name(path))
        fn = name_lbl.font(); fn.setBold(True); name_lbl.setFont(fn)
        name_lbl.setWordWrap(True)
        info.addWidget(name_lbl)
        artist = self.player._display_artist(path) or "—"
        sub = QLabel(f"{artist}   ·   {summary}")
        sub.setObjectName("dim")
        info.addWidget(sub)
        row.addLayout(info, 1)

        badge = QLabel(f"{pct}%")
        fb = badge.font(); fb.setBold(True); fb.setPointSize(13)
        badge.setFont(fb)
        badge.setStyleSheet(f"color: {t['accent']};")
        badge.setFixedWidth(52)
        badge.setAlignment(Qt.AlignCenter)
        badge.setToolTip("Схожесть")
        row.addWidget(badge)

        play_btn = QPushButton("▶")
        play_btn.setObjectName("play")
        play_btn.setFixedSize(34, 34)
        play_btn.setToolTip("Играть")
        play_btn.setCursor(Qt.PointingHandCursor)
        play_btn.clicked.connect(lambda _, p=path: self._play_local(p))
        row.addWidget(play_btn)

        dna_btn = QPushButton("🎯")
        dna_btn.setObjectName("icon")
        dna_btn.setFixedSize(34, 34)
        dna_btn.setToolTip("Открыть похожесть этого трека")
        dna_btn.setCursor(Qt.PointingHandCursor)
        dna_btn.clicked.connect(lambda _, p=path: self._open_dna_for(p))
        row.addWidget(dna_btn)

        wave_btn = QPushButton("🌊")
        wave_btn.setObjectName("icon")
        wave_btn.setFixedSize(34, 34)
        wave_btn.setToolTip("Открыть «Волну» по жанру этого трека")
        wave_btn.setCursor(Qt.PointingHandCursor)
        wave_btn.clicked.connect(lambda _, p=path: self._open_wave_for(p))
        if not self.player.internet_enabled:
            wave_btn.setEnabled(False)
        row.addWidget(wave_btn)

        return card

    def _play_source(self):
        self.player.play_path_direct(self.source_path)

    def _play_local(self, path):
        self.player.play_path_direct(path)

    def _open_dna_for(self, path):
        self.accept()
        QTimer.singleShot(10, lambda: self.player._open_similar_dialog(path))

    def _open_wave_for(self, path):
        genre = self.player._display_genre(path).strip().lower()
        self.accept()
        self.player.discover_btn.setChecked(True)
        self.player._toggle_discover(genre=genre)

    def _open_source_in_wave(self):
        self._open_wave_for(self.source_path)

    def _rescan(self):
        self.player._dna_cache.clear()
        self._load()
        self._populate_similar()


# ==================================================================
#  Встроенная панель «Волна»
# ==================================================================

class DiscoverPanel(QWidget):
    close_requested = Signal()

    def __init__(self, player):
        super().__init__()
        self.player = player
        self._net = QNetworkAccessManager(self)
        self._reply = None
        self._mode = "popular"
        self._selected_genre = ""
        self._source = "itunes"

        t = player.theme()
        main = QVBoxLayout(self)
        main.setContentsMargins(0, 0, 0, 0)
        main.setSpacing(10)

        self.card = QFrame()
        self.card.setObjectName("glassPanel")
        card_layout = QVBoxLayout(self.card)
        card_layout.setContentsMargins(0, 0, 0, 14)
        card_layout.setSpacing(10)

        self.wave = WaveWidget(t.get("wave_accent") or t["accent"],
                               t.get("wave_bg") or t["panel_rgb"])
        card_layout.addWidget(self.wave)

        ctrl = QWidget()
        cv = QVBoxLayout(ctrl)
        cv.setContentsMargins(16, 0, 16, 0)
        cv.setSpacing(10)

        modes = QHBoxLayout(); modes.setSpacing(6)
        self.mode_group = QButtonGroup(self)
        self.mode_group.setExclusive(True)
        self.mode_btns = {}
        for key, label in (("new", "🔥 Новинки"),
                            ("popular", "⭐ Популярное"),
                            ("search", "🔍 По названию")):
            b = QPushButton(label)
            b.setCheckable(True); b.setObjectName("segment")
            b.clicked.connect(lambda checked, k=key: self._set_mode(k))
            self.mode_group.addButton(b)
            self.mode_btns[key] = b
            modes.addWidget(b)
        self.mode_btns["popular"].setChecked(True)

        modes.addSpacing(12)
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Название или исполнитель…")
        self.search_edit.setClearButtonEnabled(True)
        self.search_edit.returnPressed.connect(self._search_current)
        self.search_edit.setMinimumWidth(160)
        self.search_edit.hide()
        modes.addWidget(self.search_edit, 1)

        modes.addStretch()

        self.source_combo = QComboBox()
        self.source_combo.addItem("🎵 iTunes", "itunes")
        self.source_combo.addItem("🌍 Jamendo", "jamendo")
        self.source_combo.currentIndexChanged.connect(self._on_source_change)
        modes.addWidget(self.source_combo)

        self.refresh_btn = QPushButton("↻")
        self.refresh_btn.setObjectName("icon")
        self.refresh_btn.setFixedSize(38, 34)
        self.refresh_btn.setToolTip("Обновить")
        self.refresh_btn.clicked.connect(self._search_current)
        modes.addWidget(self.refresh_btn)

        self.close_btn = QPushButton("✕")
        self.close_btn.setObjectName("icon")
        self.close_btn.setFixedSize(38, 34)
        self.close_btn.setToolTip("Закрыть волну")
        self.close_btn.clicked.connect(self.close_requested.emit)
        modes.addWidget(self.close_btn)

        cv.addLayout(modes)

        genre_row = QHBoxLayout(); genre_row.setSpacing(6)
        lbl = QLabel("Жанр:")
        f = lbl.font(); f.setBold(True); lbl.setFont(f)
        genre_row.addWidget(lbl)
        self.genres_box = QHBoxLayout(); self.genres_box.setSpacing(6)
        genre_row.addLayout(self.genres_box, 1)
        cv.addLayout(genre_row)

        card_layout.addWidget(ctrl)

        self.status = QLabel("")
        self.status.setObjectName("dim")
        self.status.setWordWrap(True)
        self.status.setContentsMargins(16, 0, 16, 0)
        card_layout.addWidget(self.status)

        self.results_scroll = QScrollArea()
        self.results_scroll.setWidgetResizable(True)
        self.results_scroll.setFrameShape(QFrame.NoFrame)
        self.results_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.results_host = QWidget()
        self.results_host_layout = QVBoxLayout(self.results_host)
        self.results_host_layout.setContentsMargins(16, 0, 16, 0)
        self.results_scroll.setWidget(self.results_host)
        card_layout.addWidget(self.results_scroll, 1)

        self.footer_hint = QLabel("")
        self.footer_hint.setObjectName("dim")
        self.footer_hint.setContentsMargins(16, 0, 16, 0)
        card_layout.addWidget(self.footer_hint)

        main.addWidget(self.card, 1)

        self._populate_genres()
        self._update_status()
        self._on_source_change(0)

    def apply_theme(self):
        t = self.player.theme()
        self.wave.set_colors(t.get("wave_accent") or t["accent"],
                             t.get("wave_bg") or t["panel_rgb"])

    def _on_source_change(self, idx):
        self._source = self.source_combo.currentData()
        if self._source == "itunes":
            self.footer_hint.setText(
                "🎵 iTunes · 30-секундные превью · кнопка ↗ — открыть полную версию")
        else:
            self.footer_hint.setText(
                "🌍 Jamendo · Creative Commons · нужен ключ в Настройках (⚙)")
        self._update_status()

    def _set_mode(self, key):
        self._mode = key
        if key == "search":
            self.search_edit.show(); self.search_edit.setFocus()
        else:
            self.search_edit.hide()
        self._search_current()

    def _populate_genres(self):
        while self.genres_box.count():
            item = self.genres_box.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        all_btn = QPushButton("Все")
        all_btn.setObjectName("secondary")
        all_btn.setCheckable(True)
        all_btn.setChecked(not self._selected_genre)
        all_btn.clicked.connect(lambda: self._select_genre(""))
        self.genres_box.addWidget(all_btn)
        genres = self.player._all_genres()
        if not genres:
            self.genres_box.addStretch(); return
        for genre, count in genres[:6]:
            btn = QPushButton(f"{genre} · {count}")
            btn.setObjectName("secondary")
            btn.clicked.connect(lambda _, g=genre: self._select_genre(g))
            self.genres_box.addWidget(btn)
        self.genres_box.addStretch()

    def _select_genre(self, genre):
        self._selected_genre = genre.strip().lower()
        self._search_current()

    def _update_status(self):
        if self._source == "jamendo" and not self.player.jamendo_key:
            self.status.setText(
                "💡 Jamendo требует ключ. Вставьте в Настройках (⚙) или "
                "переключите источник на iTunes.")
        else:
            g = f" · жанр: {self._selected_genre}" if self._selected_genre else ""
            mode = {"new": "Новинки", "popular": "Популярное",
                    "search": "Поиск"}[self._mode]
            src = "iTunes" if self._source == "itunes" else "Jamendo"
            self.status.setText(f"{src} · {mode}{g}")

    def refresh(self):
        self._populate_genres()
        self._search_current()

    def _search_current(self):
        if self._source == "jamendo":
            self._search_jamendo()
        else:
            self._search_itunes()

    def _cancel_reply(self):
        if self._reply:
            try:
                self._reply.abort(); self._reply.deleteLater()
            except Exception:
                pass
            self._reply = None

    def _search_itunes(self):
        self._clear_results()
        self._update_status()
        self.status.setText(self.status.text() + "  ·  загрузка…")
        params = {"media": "music", "entity": "song", "limit": "40", "country": "US"}
        if self._mode == "search":
            text = self.search_edit.text().strip()
            params["term"] = text if text else "top hits"
        elif self._mode == "new":
            year = datetime.now().year
            genre = self._selected_genre or "pop"
            params["term"] = f"{genre} {year}"
        else:
            params["term"] = self._selected_genre or "top hits"
        url = QUrl(ITUNES_URL + "?" + urlencode(params))
        req = QNetworkRequest(url)
        req.setHeader(QNetworkRequest.UserAgentHeader, "MusicPlayer/1.0")
        self._cancel_reply()
        self._reply = self._net.get(req)
        self._reply.finished.connect(self._on_itunes_done)

    def _search_jamendo(self):
        api_key = self.player.jamendo_key
        if not api_key:
            self._search_in_browser(); return
        self._clear_results()
        self._update_status()
        self.status.setText(self.status.text() + "  ·  загрузка…")
        params = {"client_id": api_key, "format": "json", "limit": "30",
                  "include": "musicinfo", "audioformat": "mp32"}
        if self._selected_genre:
            params["tags"] = self._selected_genre
        if self._mode == "new":
            params["order"] = "releasedate_desc"
        elif self._mode == "popular":
            params["order"] = "popularity_month"
        elif self._mode == "search":
            text = self.search_edit.text().strip()
            if text:
                params["namesearch"] = text
        url = QUrl(JAMENDO_URL + "?" + urlencode(params))
        req = QNetworkRequest(url)
        req.setHeader(QNetworkRequest.UserAgentHeader, "MusicPlayer/1.0")
        self._cancel_reply()
        self._reply = self._net.get(req)
        self._reply.finished.connect(self._on_jamendo_done)

    def _on_itunes_done(self):
        reply = self._reply; self._reply = None
        if reply is None: return
        try:
            if reply.error() != QNetworkReply.NoError:
                self.status.setText(f"Ошибка сети: {reply.errorString()}")
                reply.deleteLater(); return
            raw = bytes(reply.readAll()).decode("utf-8", errors="replace")
            data = json.loads(raw)
            self._show_results(data.get("results", []) or [])
        except Exception as e:
            self.status.setText(f"Ошибка: {e}")
            self.player._log(f"itunes error: {e!r}")
        finally:
            reply.deleteLater()

    def _on_jamendo_done(self):
        reply = self._reply; self._reply = None
        if reply is None: return
        try:
            if reply.error() != QNetworkReply.NoError:
                self.status.setText(f"Ошибка сети: {reply.errorString()}")
                reply.deleteLater(); return
            raw = bytes(reply.readAll()).decode("utf-8", errors="replace")
            data = json.loads(raw)
            self._show_results(data.get("results", []) or [])
        except Exception as e:
            self.status.setText(f"Ошибка: {e}")
            self.player._log(f"jamendo error: {e!r}")
        finally:
            reply.deleteLater()

    def _search_in_browser(self):
        text = self.search_edit.text().strip() or self._selected_genre
        q = text or "music"
        url = f"https://jamendo.com/search?q={quote_plus(q)}"
        try:
            webbrowser.open(url)
            self.status.setText(f"Нет ключа. Открываю браузер: {url}")
        except Exception as e:
            self.status.setText(f"Не удалось открыть браузер: {e}")

    def _clear_results(self):
        while self.results_host_layout.count():
            item = self.results_host_layout.takeAt(0)
            w = item.widget()
            if w: w.deleteLater()

    def _show_results(self, tracks):
        self._clear_results()
        if not tracks:
            self.status.setText("Ничего не нашлось."); return
        self._update_status()
        self.status.setText(self.status.text() + f"  ·  найдено {len(tracks)}")
        grid = QGridLayout(); grid.setSpacing(10)
        for i, tr in enumerate(tracks):
            grid.addWidget(self._make_card(tr), i // 2, i % 2)
        wrapper = QWidget()
        wrapper.setLayout(grid)
        self.results_host_layout.addWidget(wrapper)
        self.results_host_layout.addStretch()

    def _normalize(self, tr):
        if self._source == "itunes":
            return {
                "url": tr.get("previewUrl") or "",
                "title": tr.get("trackName") or "Без названия",
                "artist": tr.get("artistName") or "?",
                "dur_sec": int(tr.get("trackTimeMillis", 0)) // 1000,
                "genre": tr.get("primaryGenreName", "") or "",
                "album": tr.get("collectionName", "") or "",
                "preview": True,
                "apple_url": tr.get("trackViewUrl", "") or "",
            }
        mi = tr.get("musicinfo") or {}
        tags_list = (mi.get("tags") or {}).get("genres") or []
        return {
            "url": tr.get("audio") or "",
            "title": tr.get("name") or "Без названия",
            "artist": tr.get("artist_name") or "?",
            "dur_sec": int(tr.get("duration") or 0),
            "genre": tags_list[0] if tags_list else "",
            "album": tr.get("album_name", "") or "",
            "preview": False,
            "apple_url": "",
        }

    def _make_card(self, tr):
        d = self._normalize(tr)
        url, title, artist = d["url"], d["title"], d["artist"]
        genre, dur_sec = d["genre"], d["dur_sec"]
        is_preview = d["preview"]
        apple_url = d["apple_url"]

        card = QFrame()
        card.setObjectName("glassPanel")
        card.setMinimumHeight(96)
        card.setContextMenuPolicy(Qt.CustomContextMenu)
        card.customContextMenuRequested.connect(
            lambda pos, c=card, u=url, ti=title, ar=artist, ge=genre, au=apple_url:
            self._card_context(c, pos, u, ti, ar, ge, au))

        h = QHBoxLayout(card)
        h.setContentsMargins(12, 10, 12, 10); h.setSpacing(8)

        avatar = QLabel(); avatar.setFixedSize(52, 52)
        pix = QPixmap(52, 52); pix.fill(Qt.transparent)
        pa = QPainter(pix)
        pa.setRenderHint(QPainter.Antialiasing)
        color = QColor.fromHsv(abs(hash(artist)) % 360, 180, 210)
        pa.setBrush(color); pa.setPen(Qt.NoPen)
        pa.drawEllipse(0, 0, 52, 52)
        pa.setPen(QColor(255, 255, 255))
        f = QFont("Segoe UI", 18); f.setBold(True); pa.setFont(f)
        pa.drawText(0, 0, 52, 52, Qt.AlignCenter, artist[:1].upper())
        pa.end()
        avatar.setPixmap(pix)
        h.addWidget(avatar)

        info = QVBoxLayout(); info.setSpacing(2)
        t_lbl = QLabel(title + ("  ·  превью" if is_preview else ""))
        ft = t_lbl.font(); ft.setBold(True); t_lbl.setFont(ft)
        t_lbl.setWordWrap(True); info.addWidget(t_lbl)
        dur_str = f"{dur_sec // 60}:{dur_sec % 60:02d}" if dur_sec else ""
        parts = [artist]
        if dur_str: parts.append(dur_str)
        if genre: parts.append(genre)
        sub = QLabel("  ·  ".join(parts))
        sub.setObjectName("dim"); info.addWidget(sub)
        h.addLayout(info, 1)

        liked = url in self.player.playlists.get(DEFAULT_LIKED, [])
        like_btn = QPushButton("♥" if liked else "♡")
        like_btn.setObjectName("like")
        like_btn.setFixedSize(34, 34)
        like_btn.setFont(self.player._icon_font(13))
        like_btn.setToolTip("В Понравившиеся")
        like_btn.setCursor(Qt.PointingHandCursor)
        like_btn.setProperty("liked", "true" if liked else "false")
        like_btn.clicked.connect(
            lambda _, u=url, ti=title, ar=artist, ge=genre, b=like_btn:
            self._toggle_like(u, ti, ar, ge, b))
        h.addWidget(like_btn)

        add_btn = QPushButton("＋")
        add_btn.setObjectName("icon")
        add_btn.setFixedSize(34, 34)
        add_btn.setToolTip("В плейлист")
        add_btn.setCursor(Qt.PointingHandCursor)
        add_btn.clicked.connect(
            lambda _, u=url, ti=title, ar=artist, ge=genre:
            self._add_menu(u, ti, ar, ge))
        h.addWidget(add_btn)

        ext_btn = QPushButton("↗")
        ext_btn.setObjectName("icon")
        ext_btn.setFixedSize(34, 34)
        ext_btn.setToolTip("Открыть полную версию")
        ext_btn.setCursor(Qt.PointingHandCursor)
        ext_btn.clicked.connect(
            lambda _, ti=title, ar=artist, au=apple_url:
            self._external_menu(ti, ar, au))
        h.addWidget(ext_btn)

        play_btn = QPushButton("▶")
        play_btn.setObjectName("play")
        play_btn.setFixedSize(40, 40)
        play_btn.setToolTip("Играть здесь")
        play_btn.setCursor(Qt.PointingHandCursor)
        play_btn.clicked.connect(
            lambda _, u=url, ti=title, ar=artist:
            self._play(u, ti, ar))
        h.addWidget(play_btn)

        return card

    def _card_context(self, card, pos, url, title, artist, genre, apple_url):
        menu = QMenu(self)
        menu.setStyleSheet(self.player.styleSheet())
        global_pos = card.mapToGlobal(pos)

        menu.addAction("▶  Играть", lambda: self._play(url, title, artist))
        menu.addSeparator()
        menu.addAction("✎  Информация о треке…",
                       lambda: self._card_info(url, title, artist, genre))
        menu.addAction("📄  Текст", lambda: self._card_lyrics(url, title, artist))
        menu.addSeparator()
        menu.addAction("🎵  Найти на Genius",
                       lambda: self._search_genius(title, artist))
        menu.addAction("🔍  Найти в Google",
                       lambda: self._search_google(title, artist))
        menu.addSeparator()
        liked = url in self.player.playlists.get(DEFAULT_LIKED, [])
        menu.addAction(("💔  Убрать из избранного" if liked else "❤  В понравившиеся"),
                       lambda: self._toggle_like_simple(url, title, artist, genre))
        menu.addAction("＋  Добавить в плейлист…",
                       lambda: self._add_menu(url, title, artist, genre))
        if apple_url:
            menu.addSeparator()
            menu.addAction("🍎  Открыть в Apple Music",
                           lambda: webbrowser.open(apple_url))
        menu.exec(global_pos)

    def _card_info(self, url, title, artist, genre):
        cur_meta = self.player.metadata.get(url, {})
        cur_name = cur_meta.get("display_name", title)
        cur_artist = cur_meta.get("artist", artist)
        cur_genre = cur_meta.get("genre", genre)
        dlg = TrackInfoDialog(self, cur_name, cur_artist, cur_genre)
        if dlg.exec() != QDialog.Accepted:
            return
        name, ar, ge = dlg.values()
        meta = self.player.metadata.setdefault(url, {})
        if name: meta["display_name"] = name
        if ar: meta["artist"] = ar
        if ge: meta["genre"] = ge
        self.player.save_config()
        self.status.setText(f"✓ Обновлено: {name or title}")

    def _card_lyrics(self, url, title, artist):
        if url not in self.player.metadata:
            self.player.metadata[url] = {}
        self.player.metadata[url].setdefault("display_name", title)
        self.player.metadata[url].setdefault("artist", artist)
        self.player._open_lyrics(url)

    def _search_genius(self, title, artist):
        query = f"{title} {artist}".strip()
        try:
            webbrowser.open(f"https://genius.com/search?q={quote_plus(query)}")
            self.status.setText(f"🎵 Genius: {query}")
        except Exception as e:
            self.status.setText(f"Не удалось открыть браузер: {e}")

    def _search_google(self, title, artist):
        query = f"{title} {artist}".strip()
        try:
            webbrowser.open(f"https://www.google.com/search?q={quote_plus(query)}")
            self.status.setText(f"🔍 Google: {query}")
        except Exception as e:
            self.status.setText(f"Не удалось открыть браузер: {e}")

    def _toggle_like_simple(self, url, title, artist, genre):
        liked = self.player.playlists[DEFAULT_LIKED]
        if url in liked:
            liked.remove(url)
            self.status.setText(f"💔 Убрано: {title}")
        else:
            liked.append(url)
            if url not in self.player.metadata:
                self.player.metadata[url] = {}
            self.player.metadata[url]["display_name"] = title
            self.player.metadata[url]["artist"] = artist
            if genre:
                self.player.metadata[url]["genre"] = genre
            self.status.setText(f"❤ В «Понравившиеся»: {title}")
        self.player.save_config()
        if self.player.active_playlist == DEFAULT_LIKED:
            self.player.rebuild_playlist()

    def _external_menu(self, title, artist, apple_url):
        query = f"{title} {artist}".strip()
        menu = QMenu(self)
        menu.setStyleSheet(self.player.styleSheet())
        if apple_url:
            menu.addAction("🍎  Apple Music (этот трек)",
                           lambda: webbrowser.open(apple_url))
        else:
            menu.addAction("🍎  Apple Music (поиск)",
                           lambda: webbrowser.open(
                               f"https://music.apple.com/search?term={quote_plus(query)}"))
        menu.addAction("▶️  YouTube Music",
                       lambda: webbrowser.open(
                           f"https://music.youtube.com/search?q={quote_plus(query)}"))
        menu.addAction("💚  Spotify",
                       lambda: webbrowser.open(
                           f"https://open.spotify.com/search/{quote_plus(query)}"))
        menu.addSeparator()
        menu.addAction("🎵  Genius",
                       lambda: webbrowser.open(
                           f"https://genius.com/search?q={quote_plus(query)}"))
        menu.addAction("🔍  Google",
                       lambda: webbrowser.open(
                           f"https://www.google.com/search?q={quote_plus(query)}"))
        menu.exec(QCursor.pos())

    def _toggle_like(self, url, title, artist, genre, btn):
        if url in self.player.playlists[DEFAULT_LIKED]:
            self.player.playlists[DEFAULT_LIKED].remove(url)
            btn.setText("♡"); btn.setProperty("liked", "false")
            self.status.setText(f"💔 Убрано: {title}")
        else:
            self.player.playlists[DEFAULT_LIKED].append(url)
            if url not in self.player.metadata:
                self.player.metadata[url] = {}
            self.player.metadata[url]["display_name"] = title
            self.player.metadata[url]["artist"] = artist
            if genre:
                self.player.metadata[url]["genre"] = genre
            btn.setText("♥"); btn.setProperty("liked", "true")
            self.status.setText(f"❤ В «Понравившиеся»: {title}")
        btn.style().unpolish(btn); btn.style().polish(btn)
        self.player.save_config()
        if self.player.active_playlist == DEFAULT_LIKED:
            self.player.rebuild_playlist()

    def _add_menu(self, url, title, artist, genre):
        menu = QMenu(self)
        menu.setStyleSheet(self.player.styleSheet())
        added = False
        for name in self.player.playlists:
            if name == DEFAULT_LIKED:
                continue
            act = menu.addAction(f"＋ В «{name}»")
            act.triggered.connect(
                lambda checked=False, n=name:
                self._add_to_playlist(url, n, title, artist, genre))
            added = True
        if not added:
            a = menu.addAction("Нет плейлистов"); a.setEnabled(False)
        menu.addSeparator()
        act_new = menu.addAction("＋ Создать плейлист…")
        act_new.triggered.connect(
            lambda: self._create_and_add(url, title, artist, genre))
        menu.exec(QCursor.pos())

    def _add_to_playlist(self, url, name, title, artist, genre):
        pl = self.player.playlists.get(name)
        if pl is None: return
        if url in pl:
            self.status.setText(f"Уже в «{name}»: {title}"); return
        pl.append(url)
        if url not in self.player.metadata:
            self.player.metadata[url] = {}
        self.player.metadata[url]["display_name"] = title
        self.player.metadata[url]["artist"] = artist
        if genre:
            self.player.metadata[url]["genre"] = genre
        self.player.save_config()
        if self.player.active_playlist == name:
            self.player.rebuild_playlist()
        self.status.setText(f"✓ В «{name}»: {title}")

    def _create_and_add(self, url, title, artist, genre):
        name, ok = QInputDialog.getText(self, "Новый плейлист", "Название:")
        if not ok or not name.strip(): return
        name = name.strip()
        if name == DEFAULT_LIKED:
            QMessageBox.warning(self, "Внимание", "Имя зарезервировано"); return
        if name in self.player.playlists:
            QMessageBox.warning(self, "Внимание", "Уже есть"); return
        self.player.playlists[name] = []
        self._add_to_playlist(url, name, title, artist, genre)

    def _play(self, url, title, artist):
        if not url:
            self.status.setText("Нет аудио для этой записи"); return
        self.player._play_stream(url, title, artist)
        self.status.setText(f"▶ {title} — {artist}")


# ==================================================================
#  Встроенная панель «Отчёты» (с вкладкой «Из Волны»)
# ==================================================================

class ReportsPanel(QWidget):
    close_requested = Signal()

    def __init__(self, player):
        super().__init__()
        self.player = player
        self.mode = "week"

        t = player.theme()
        self.text_color = t["text"]
        self.accent_color = t["accent"]
        self.palette = self._make_palette()

        main = QVBoxLayout(self)
        main.setContentsMargins(0, 0, 0, 0)
        main.setSpacing(10)

        card = QFrame()
        card.setObjectName("glassPanel")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(18, 18, 18, 18)
        card_layout.setSpacing(12)

        top = QHBoxLayout(); top.setSpacing(8)
        self.mode_group = QButtonGroup(self)
        self.mode_group.setExclusive(True)
        self.mode_btns = {}
        for key, label, tip in (
            ("day", "День", "Статистика за день (локальные файлы)"),
            ("week", "Неделя", "Статистика за неделю (локальные файлы)"),
            ("month", "Месяц", "Статистика за месяц (локальные файлы)"),
            ("wave", "🌊 Из Волны", "Статистика по стримам из вкладки «Волна»"),
        ):
            b = QPushButton(label)
            b.setCheckable(True); b.setObjectName("segment")
            b.setToolTip(tip)
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
        close_btn = QPushButton("✕")
        close_btn.setObjectName("icon")
        close_btn.setFixedSize(38, 34)
        close_btn.setToolTip("Закрыть отчёты")
        close_btn.clicked.connect(self.close_requested.emit)
        top.addWidget(close_btn)

        card_layout.addLayout(top)

        cards = QHBoxLayout(); cards.setSpacing(10)
        self.card_time = self._make_card("Время прослушивания")
        self.card_count = self._make_card("Треков прослушано")
        self.card_artists = self._make_card("Уникальных исполнителей")
        self.card_compare = self._make_card("Сравнение с прошлым")
        for c in (self.card_time, self.card_count, self.card_artists, self.card_compare):
            cards.addWidget(c)
        card_layout.addLayout(cards)

        pies = QHBoxLayout(); pies.setSpacing(10)
        self.pie_tracks = PieChartWidget("Топ треков", self.text_color, self.palette)
        self.pie_artists = PieChartWidget("Топ исполнителей", self.text_color, self.palette)
        pies.addWidget(self.pie_tracks, 1)
        pies.addWidget(self.pie_artists, 1)
        card_layout.addLayout(pies, 1)

        self.bar_chart = BarChartWidget("Активность", self.text_color, self.accent_color)
        self.bar_chart.setMinimumHeight(150)
        card_layout.addWidget(self.bar_chart)

        main.addWidget(card, 1)
        self._refresh()

    def _make_palette(self):
        accent = QColor(self.accent_color)
        base_hue = accent.hue()
        base_sat = max(150, accent.saturation())
        return [QColor.fromHsv((base_hue + i * 45) % 360, base_sat,
                                225 if i % 2 == 0 else 180).name()
                for i in range(7)]

    def _make_card(self, title):
        t = self.player.theme()
        card = QFrame(); card.setObjectName("glassPanel")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(14, 10, 14, 10)
        title_lbl = QLabel(title)
        title_lbl.setStyleSheet(f"color: {t['text_dim']}; font-size: 11px;")
        value_lbl = QLabel("—")
        f = value_lbl.font(); f.setPointSize(15); f.setBold(True)
        value_lbl.setFont(f)
        value_lbl.setStyleSheet(f"color: {t['text']};")
        layout.addWidget(title_lbl); layout.addWidget(value_lbl)
        card._value_lbl = value_lbl
        card._title_lbl = title_lbl
        return card

    def _on_mode_click(self, key):
        self.mode = key; self._refresh()

    def _get_period(self):
        qd = self.date_edit.date()
        d = datetime(qd.year(), qd.month(), qd.day())
        if self.mode == "day":
            start = d; end = start + timedelta(days=1)
        elif self.mode in ("week", "wave"):
            monday = d - timedelta(days=d.weekday())
            start = monday; end = start + timedelta(days=7)
        else:
            start = datetime(d.year, d.month, 1)
            end = (datetime(d.year + 1, 1, 1) if d.month == 12
                   else datetime(d.year, d.month + 1, 1))
        return start.timestamp(), end.timestamp()

    def _aggregate(self, start_ts, end_ts, wave_only=False):
        """wave_only=True → только стримы (http/https). Иначе — только локальные."""
        counts = {}; artists = {}; total_dur = 0.0; total_count = 0
        for e in self.player.history:
            ts = e.get("ts", 0)
            if not (start_ts <= ts < end_ts):
                continue
            path = e["path"]
            is_wave = (path.startswith("http://")
                       or path.startswith("https://"))
            if wave_only and not is_wave:
                continue
            if not wave_only and is_wave:
                continue
            counts[path] = counts.get(path, 0) + 1
            artist = self.player._display_artist(path) or "Неизвестный"
            artists[artist] = artists.get(artist, 0) + 1
            total_dur += e.get("dur", 0)
            total_count += 1
        return counts, artists, total_dur, total_count

    def _refresh(self):
        wave_mode = (self.mode == "wave")

        if wave_mode:
            self.card_time._title_lbl.setText("Время из Волны")
            self.card_count._title_lbl.setText("Стримов прослушано")
            self.card_artists._title_lbl.setText("Исполнителей из Волны")
            self.card_compare._title_lbl.setText("Разных из Волны")
            self.pie_tracks.set_title("Топ из Волны")
            self.pie_artists.set_title("Топ исполнителей из Волны")
            self.bar_chart.set_title("Активность (Волна)")
        else:
            self.card_time._title_lbl.setText("Время прослушивания")
            self.card_count._title_lbl.setText("Треков прослушано")
            self.card_artists._title_lbl.setText("Уникальных исполнителей")
            self.card_compare._title_lbl.setText("Сравнение с прошлым")
            self.pie_tracks.set_title("Топ треков")
            self.pie_artists.set_title("Топ исполнителей")
            self.bar_chart.set_title("Активность")

        start_ts, end_ts = self._get_period()
        counts, artists, total_dur, total_count = self._aggregate(
            start_ts, end_ts, wave_only=wave_mode)
        self.card_time._value_lbl.setText(self._fmt_duration(total_dur))
        self.card_count._value_lbl.setText(str(total_count))
        self.card_artists._value_lbl.setText(str(len(artists)))

        if wave_mode:
            # Уникальных треков из Волны
            self.card_compare._value_lbl.setText(str(len(counts)))
        else:
            # Сравнение с предыдущим периодом (только локальные)
            _, _, prev_dur, _ = self._aggregate(
                start_ts - (end_ts - start_ts), start_ts, wave_only=False)
            if prev_dur > 0:
                delta = (total_dur - prev_dur) / prev_dur * 100
                sign = "+" if delta >= 0 else ""
                self.card_compare._value_lbl.setText(f"{sign}{delta:.0f}%")
            else:
                self.card_compare._value_lbl.setText("—")

        top_tracks = self._top_n(counts, 5)
        top_artists = self._top_n(artists, 5)
        named_tracks = [(k if k == "Другие" else self.player._display_name(k), c)
                        for k, c in top_tracks]
        self.pie_tracks.set_data(named_tracks)
        self.pie_artists.set_data(top_artists)
        self._update_bar_chart(start_ts, end_ts)

    def _top_n(self, items, n=5):
        sorted_items = sorted(items.items(), key=lambda x: -x[1])
        if len(sorted_items) <= n:
            return sorted_items
        top = sorted_items[:n]
        top.append(("Другие", sum(v for _, v in sorted_items[n:])))
        return top

    def _update_bar_chart(self, start_ts, end_ts):
        wave_mode = (self.mode == "wave")

        def is_wave(path):
            return path.startswith("http://") or path.startswith("https://")

        if self.mode == "day":
            values = [0] * 24
            labels = [f"{h:02d}" for h in range(24)]
            for e in self.player.history:
                ts = e.get("ts", 0)
                if not (start_ts <= ts < end_ts):
                    continue
                if wave_mode != is_wave(e["path"]):
                    continue
                values[datetime.fromtimestamp(ts).hour] += 1
        elif self.mode in ("week", "wave"):
            values = [0] * 7
            labels = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]
            for e in self.player.history:
                ts = e.get("ts", 0)
                if not (start_ts <= ts < end_ts):
                    continue
                if wave_mode != is_wave(e["path"]):
                    continue
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
                if not (start_ts <= ts < end_ts):
                    continue
                if wave_mode != is_wave(e["path"]):
                    continue
                d = datetime.fromtimestamp(ts).date()
                idx = (d - start_date).days
                if 0 <= idx < days:
                    values[idx] += 1
        highlight = values.index(max(values)) if values and max(values) > 0 else -1
        self.bar_chart.set_data(values, labels, highlight)

    def refresh(self):
        self._refresh()

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


# ==================================================================
#  Настройки
# ==================================================================

class ColorSettingsDialog(QDialog):
    def __init__(self, player):
        super().__init__(player)
        self.player = player
        self.setWindowTitle("⚙  Настройки")
        self.setStyleSheet(player.styleSheet())
        self.resize(580, 0)
        self.setMinimumWidth(560)

        base = THEMES[player._theme_name]
        override = player.theme_overrides.get(player._theme_name, {})

        self.accent      = QColor(override.get("accent", base["accent"]))
        self.panel_rgb   = QColor(*override.get("panel_rgb", base["panel_rgb"]))
        self.panel_alpha = int(override.get("panel_alpha", base["panel_alpha"]))
        self.lyrics_text = QColor(override.get("lyrics_text", base["lyrics_text"]))
        self.lyrics_bg   = QColor(override.get("lyrics_bg", base["lyrics_bg"]))
        self.search_text = QColor(override.get("search_text", base["search_text"]))
        self.search_bg   = QColor(override.get("search_bg", base["search_bg"]))
        self.liked_bg    = QColor(override.get("liked_bg", base["liked_bg"]))
        self.stats_text  = QColor(override.get("stats_text", base["stats_text"]))
        self.wave_accent = QColor(override.get("wave_accent") or base.get("wave_accent") or base["accent"])
        self.wave_bg     = QColor(override.get("wave_bg") or base.get("wave_bg") or "#0e0e12")

        main = QVBoxLayout(self)
        main.setSpacing(10); main.setContentsMargins(14, 14, 14, 14)

        gb_visual = QGroupBox("🎵  Визуализация (Волна)")
        fv = QFormLayout(gb_visual)
        fv.setContentsMargins(14, 22, 14, 12); fv.setSpacing(8)

        self.live_wave_check = QCheckBox("Реакция на бит (живой спектр)")
        analyzer = getattr(player, "spectrum_analyzer", None)
        capable = bool(analyzer and analyzer.is_available())
        self.live_wave_check.setChecked(bool(player.live_wave_enabled))
        if not capable:
            self.live_wave_check.setEnabled(False)
            self.live_wave_check.setText(
                "Реакция на бит (недоступно — нужен PySide6 6.8+)")
        else:
            numpy_status = "numpy ✓" if analyzer.using_numpy() else "numpy ✗ (медленнее)"
            self.live_wave_check.setToolTip(
                f"Включает FFT-анализ аудио и детекцию бита.\n"
                f"Анализатор: {'OK' if capable else 'недоступен'}\n"
                f"Ускорение: {numpy_status}\n\n"
                f"Выключите, если хотите классическую плавную волну.")
        fv.addRow("", self.live_wave_check)

        hint = QLabel(
            "💡 Для плавной работы установите <code>pip install numpy</code>"
            if capable and not (analyzer and analyzer.using_numpy())
            else "")
        hint.setWordWrap(True)
        hint.setStyleSheet(f"color: {base.get('text_dim', '#8a8a95')}; font-size: 10px;")
        fv.addRow("", hint)

        self.wave_accent_btn = QPushButton(); self.wave_accent_btn.clicked.connect(self._pick_wave_accent)
        self._update_color_btn(self.wave_accent_btn, self.wave_accent)
        fv.addRow("Цвет волн:", self.wave_accent_btn)
        self.wave_bg_btn = QPushButton(); self.wave_bg_btn.clicked.connect(self._pick_wave_bg)
        self._update_color_btn(self.wave_bg_btn, self.wave_bg)
        fv.addRow("Фон визуализации:", self.wave_bg_btn)
        main.addWidget(gb_visual)

        gb_basic = QGroupBox("🎨  Основные цвета")
        fb = QFormLayout(gb_basic)
        fb.setContentsMargins(14, 22, 14, 12); fb.setSpacing(8)
        self.accent_btn = QPushButton(); self.accent_btn.clicked.connect(self._pick_accent)
        self._update_color_btn(self.accent_btn, self.accent)
        fb.addRow("Акцентный цвет:", self.accent_btn)
        self.panel_btn = QPushButton(); self.panel_btn.clicked.connect(self._pick_panel)
        self._update_color_btn(self.panel_btn, self.panel_rgb)
        fb.addRow("Цвет панелей:", self.panel_btn)
        alpha_row = QHBoxLayout()
        self.alpha_slider = QSlider(Qt.Horizontal)
        self.alpha_slider.setRange(0, 255); self.alpha_slider.setValue(self.panel_alpha)
        self.alpha_label = QLabel(str(self.panel_alpha)); self.alpha_label.setMinimumWidth(34)
        self.alpha_slider.valueChanged.connect(lambda v: self.alpha_label.setText(str(v)))
        alpha_row.addWidget(self.alpha_slider, 1); alpha_row.addWidget(self.alpha_label)
        fb.addRow("Прозрачность (0–255):", alpha_row)
        main.addWidget(gb_basic)

        gb_search = QGroupBox("🔍  Поисковая строка")
        fs = QFormLayout(gb_search)
        fs.setContentsMargins(14, 22, 14, 12); fs.setSpacing(8)
        self.search_text_btn = QPushButton(); self.search_text_btn.clicked.connect(self._pick_search_text)
        self._update_color_btn(self.search_text_btn, self.search_text)
        fs.addRow("Цвет текста:", self.search_text_btn)
        self.search_bg_btn = QPushButton(); self.search_bg_btn.clicked.connect(self._pick_search_bg)
        self._update_color_btn(self.search_bg_btn, self.search_bg)
        fs.addRow("Фон строки:", self.search_bg_btn)
        main.addWidget(gb_search)

        gb_liked = QGroupBox("⭐  Понравившиеся и счётчик")
        flk = QFormLayout(gb_liked)
        flk.setContentsMargins(14, 22, 14, 12); flk.setSpacing(8)
        self.liked_bg_btn = QPushButton(); self.liked_bg_btn.clicked.connect(self._pick_liked_bg)
        self._update_color_btn(self.liked_bg_btn, self.liked_bg)
        flk.addRow("Фон кнопки «Понравившиеся»:", self.liked_bg_btn)
        self.stats_text_btn = QPushButton(); self.stats_text_btn.clicked.connect(self._pick_stats_text)
        self._update_color_btn(self.stats_text_btn, self.stats_text)
        flk.addRow("Текст счётчика:", self.stats_text_btn)
        main.addWidget(gb_liked)

        gb_lyrics = QGroupBox("📄  Текст песни")
        fl = QFormLayout(gb_lyrics)
        fl.setContentsMargins(14, 22, 14, 12); fl.setSpacing(8)
        self.lyrics_text_btn = QPushButton(); self.lyrics_text_btn.clicked.connect(self._pick_lyrics_text)
        self._update_color_btn(self.lyrics_text_btn, self.lyrics_text)
        fl.addRow("Цвет текста:", self.lyrics_text_btn)
        self.lyrics_bg_btn = QPushButton(); self.lyrics_bg_btn.clicked.connect(self._pick_lyrics_bg)
        self._update_color_btn(self.lyrics_bg_btn, self.lyrics_bg)
        fl.addRow("Фон панели:", self.lyrics_bg_btn)
        main.addWidget(gb_lyrics)

        gb_online = QGroupBox("🌊  Онлайн-рекомендации (Jamendo)")
        fo = QFormLayout(gb_online)
        fo.setContentsMargins(14, 22, 14, 12); fo.setSpacing(8)
        self.jamendo_edit = QLineEdit(player.jamendo_key)
        self.jamendo_edit.setPlaceholderText("client_id с devportal.jamendo.com")
        fo.addRow("API-ключ:", self.jamendo_edit)
        link = QLabel(f'<a href="{JAMENDO_KEY_URL}" style="color:{self.accent.name()};">'
                      f'Получить ключ (бесплатно)</a>')
        link.setOpenExternalLinks(True)
        fo.addRow("", link)
        main.addWidget(gb_online)

        gb_bg = QGroupBox("🖼  Фон окна")
        fbg = QHBoxLayout(gb_bg)
        fbg.setContentsMargins(14, 22, 14, 12); fbg.setSpacing(8)
        bg_btn = QPushButton("🖼  Изменить фон"); bg_btn.clicked.connect(self._change_bg)
        fbg.addWidget(bg_btn)
        self.remove_bg_btn = QPushButton("✕  Убрать фон")
        self.remove_bg_btn.clicked.connect(self._remove_bg)
        self.remove_bg_btn.setEnabled(bool(player.background_path))
        fbg.addWidget(self.remove_bg_btn); fbg.addStretch()
        main.addWidget(gb_bg)

        faq_row = QHBoxLayout()
        faq_btn = QPushButton("❓  FAQ — частые вопросы")
        faq_btn.clicked.connect(self._open_faq)
        faq_row.addWidget(faq_btn); faq_row.addStretch()
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
        c = QColorDialog.getColor(self.accent, self, "Акцент")
        if c.isValid(): self.accent = c; self._update_color_btn(self.accent_btn, c)

    def _pick_panel(self):
        c = QColorDialog.getColor(self.panel_rgb, self, "Панели")
        if c.isValid(): self.panel_rgb = c; self._update_color_btn(self.panel_btn, c)

    def _pick_search_text(self):
        c = QColorDialog.getColor(self.search_text, self, "Текст поиска")
        if c.isValid(): self.search_text = c; self._update_color_btn(self.search_text_btn, c)

    def _pick_search_bg(self):
        c = QColorDialog.getColor(self.search_bg, self, "Фон поиска")
        if c.isValid(): self.search_bg = c; self._update_color_btn(self.search_bg_btn, c)

    def _pick_liked_bg(self):
        c = QColorDialog.getColor(self.liked_bg, self, "Фон Понравившиеся")
        if c.isValid(): self.liked_bg = c; self._update_color_btn(self.liked_bg_btn, c)

    def _pick_stats_text(self):
        c = QColorDialog.getColor(self.stats_text, self, "Текст счётчика")
        if c.isValid(): self.stats_text = c; self._update_color_btn(self.stats_text_btn, c)

    def _pick_lyrics_text(self):
        c = QColorDialog.getColor(self.lyrics_text, self, "Текст песни")
        if c.isValid(): self.lyrics_text = c; self._update_color_btn(self.lyrics_text_btn, c)

    def _pick_lyrics_bg(self):
        c = QColorDialog.getColor(self.lyrics_bg, self, "Фон текста")
        if c.isValid(): self.lyrics_bg = c; self._update_color_btn(self.lyrics_bg_btn, c)

    def _pick_wave_accent(self):
        c = QColorDialog.getColor(self.wave_accent, self, "Цвет волн")
        if c.isValid(): self.wave_accent = c; self._update_color_btn(self.wave_accent_btn, c)

    def _pick_wave_bg(self):
        c = QColorDialog.getColor(self.wave_bg, self, "Фон визуализации")
        if c.isValid(): self.wave_bg = c; self._update_color_btn(self.wave_bg_btn, c)

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
        self.player.apply_theme(); self.player.save_config(); self.accept()

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
            "wave_accent":  self.wave_accent.name(),
            "wave_bg":      self.wave_bg.name(),
        }
        self.player.jamendo_key = self.jamendo_edit.text().strip()
        if self.live_wave_check.isEnabled():
            self.player.live_wave_enabled = self.live_wave_check.isChecked()
            self.player._apply_live_wave_setting()
        self.player.apply_theme(); self.player.save_config(); self.accept()


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
                self.update(); return
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
        self.resize(1280, 860)
        self.setMinimumSize(820, 700)

        self.player = QMediaPlayer(self)
        self.audio  = QAudioOutput(self)
        self.player.setAudioOutput(self.audio)

        self.live_wave_enabled = True
        self.spectrum_analyzer = AudioSpectrumAnalyzer(self.player, self)
        self.spectrum_analyzer.audio_stats_ready.connect(self._on_audio_stats)

        self._theme_name      = DEFAULT_THEME
        self._saved_vol       = 70
        self.internet_enabled = True
        self.playlists        = {DEFAULT_LIKED: [], DEFAULT_PLAYLIST: []}
        self.active_playlist  = DEFAULT_PLAYLIST
        self.playlist         = self.playlists[self.active_playlist]
        self.metadata         = {}
        self.theme_overrides  = {}
        self.background_path  = ""
        self.jamendo_key      = ""
        self.current_index    = -1
        self._dragging_seek   = False
        self._advancing       = False
        self.track_rows       = []

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
        self._dna_cache      = {}
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

        self._apply_live_wave_setting()

        self.player.positionChanged.connect(self._on_position)
        self.player.durationChanged.connect(self._on_duration)
        self.player.mediaStatusChanged.connect(self._on_media_status)
        self.player.playbackStateChanged.connect(self._on_state)
        self.player.errorOccurred.connect(self._on_error)

        self.audio.setVolume(self._saved_vol / 100)
        self.volume_slider.setValue(self._saved_vol)
        self._update_volume_label(self._saved_vol)
        self._volume_save_timer.stop()

        self._log(f"=== start, live_fft: {self.spectrum_analyzer.is_available()}, "
                  f"numpy: {self.spectrum_analyzer.using_numpy()}, "
                  f"live_enabled: {self.live_wave_enabled} ===")

    def _on_audio_stats(self, bass, mid, high, beat, amp):
        if hasattr(self, "discover_panel"):
            self.discover_panel.wave.set_beat_stats(bass, mid, high, beat, amp)

    def _apply_live_wave_setting(self):
        use_live = bool(self.live_wave_enabled) and self.spectrum_analyzer.is_available()
        self.spectrum_analyzer.set_enabled(use_live)
        if hasattr(self, "discover_panel"):
            self.discover_panel.wave.set_live_enabled(use_live)
            self.discover_panel.wave.set_live_capable(
                self.spectrum_analyzer.is_available())

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
                      "search_text", "search_bg", "liked_bg", "stats_text",
                      "wave_accent", "wave_bg"):
                if k in ov:
                    base[k] = ov[k] if k != "panel_rgb" else tuple(ov[k])
        if not base.get("wave_accent"):
            base["wave_accent"] = base["accent"]
        if not base.get("wave_bg"):
            r, g, b = base["panel_rgb"]
            base["wave_bg"] = "#{:02x}{:02x}{:02x}".format(
                max(0, r // 3), max(0, g // 3), max(0, b // 3))
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
            self.jamendo_key = str(data.get("jamendo_key", "")).strip()
            self.live_wave_enabled = bool(data.get("live_wave_enabled", True))
            if "playlists" not in data and "playlist" in data:
                self.playlists = {DEFAULT_LIKED: [],
                                  DEFAULT_PLAYLIST: list(data.get("playlist", []))}
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
                "jamendo_key":      self.jamendo_key,
                "live_wave_enabled": self.live_wave_enabled,
            }
            tmp = CONFIG_FILE.with_suffix(".json.tmp")
            tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2),
                           encoding="utf-8")
            os.replace(tmp, CONFIG_FILE)
        except Exception as e:
            self._log("save_config: " + repr(e))

    def load_history(self):
        try:
            CONFIG_DIR.mkdir(parents=True, exist_ok=True)
            if not HISTORY_FILE.exists():
                HISTORY_FILE.write_text("[]", encoding="utf-8"); return
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
        """Фиксирует проигранный трек в историю. Работает и для локальных, и для стримов."""
        path = self._playing_path
        started_at = self._play_started_at
        self._playing_path = None
        self._play_started_at = None
        if not path or started_at is None:
            return
        dur_ms = self.player.duration()
        if dur_ms <= 0:
            dur_ms = self._current_duration_ms
        dur_sec = dur_ms / 1000.0
        if dur_sec <= 0:
            return
        if force_dur is not None:
            listened = force_dur
        else:
            pos_sec = self.player.position() / 1000.0
            if pos_sec <= 0:
                pos_sec = dur_sec
            listened = min(pos_sec, dur_sec)
        threshold = min(30.0, max(5.0, dur_sec * 0.3))
        if listened < threshold:
            return
        self.history.append({"path": path, "ts": started_at,
                              "dur": round(listened, 1)})
        self._trim_history(); self.save_history()

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
            background-color: {t['accent']}; color: #ffffff;
            border: none; border-radius: 12px;
            padding: 8px 14px; font-size: 12px; font-weight: bold;
        }}
        QPushButton:hover {{ background-color: {t['accent_hover']}; }}
        QPushButton:disabled {{ background-color: {t['surface']}; color: {t['text_dim']}; }}

        QPushButton#secondary {{
            background-color: {t['surface']}; color: {t['text']}; font-weight: normal;
        }}
        QPushButton#secondary:hover {{ background-color: {t['accent']}; color: white; }}
        QPushButton#secondary:checked {{ background-color: {t['accent']}; color: white; }}

        QPushButton#icon {{
            background-color: {t['surface']}; color: {t['text']};
            font-size: 13px; padding: 0px;
        }}
        QPushButton#icon:hover {{ background-color: {t['accent']}; color: white; }}

        QPushButton#liked_btn {{
            background-color: {t['liked_bg']}; color: #ffffff;
            font-size: 13px; padding: 0px;
            border-radius: 12px; border: none;
        }}
        QPushButton#liked_btn:hover {{ background-color: {liked_hover}; }}

        QPushButton#net {{
            background-color: {t['surface']}; color: {t['text_dim']};
            font-size: 13px; padding: 0px; border-radius: 12px; border: none;
        }}
        QPushButton#net[online="true"] {{ color: {t['accent']}; }}
        QPushButton#net:hover {{ background-color: {t['accent']}; color: white; }}

        QPushButton#like {{
            background-color: transparent; color: {t['text_dim']};
            font-size: 16px; border-radius: 8px; padding: 0px;
        }}
        QPushButton#like:hover {{ background-color: {t['surface']}; }}
        QPushButton#like[liked="true"] {{ color: {t['accent']}; }}

        QPushButton#play {{
            background-color: {t['accent']}; color: white;
            font-size: 16px; border-radius: 16px; padding: 0px;
        }}
        QPushButton#play:hover {{ background-color: {t['accent_hover']}; }}

        QPushButton#segment {{
            background-color: {t['surface']}; color: {t['text']};
            font-weight: normal; border: none; border-radius: 10px;
            padding: 6px 14px;
        }}
        QPushButton#segment:checked {{
            background-color: {t['accent']}; color: #ffffff; font-weight: bold;
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
            background-color: {t['search_bg']}; color: {t['search_text']};
            border: 1px solid rgba(255,255,255,25);
            border-radius: 12px; padding: 8px 12px; font-size: 12px;
            selection-background-color: {t['accent']}; selection-color: #ffffff;
        }}
        QLineEdit:focus {{ border: 1px solid {t['accent']}; }}

        QComboBox {{
            background-color: {t['surface']}; color: {t['text']};
            border: 1px solid rgba(255,255,255,25); border-radius: 10px;
            padding: 6px 10px; font-size: 11px;
        }}
        QComboBox::drop-down {{ border: none; width: 16px; }}
        QComboBox QAbstractItemView {{
            background-color: {t['search_bg']}; color: {t['text']};
            selection-background-color: {t['accent']}; selection-color: white;
            border-radius: 8px;
        }}

        QCheckBox {{
            color: {t['text']}; font-size: 12px; spacing: 8px;
        }}
        QCheckBox::indicator {{
            width: 16px; height: 16px; border-radius: 4px;
            border: 1px solid rgba(255,255,255,40);
            background: {t['surface']};
        }}
        QCheckBox::indicator:checked {{
            background: {t['accent']};
            border: 1px solid {t['accent']};
        }}

        QDateEdit {{
            background-color: {t['search_bg']}; color: {t['search_text']};
            border: 1px solid rgba(255,255,255,25); border-radius: 10px;
            padding: 6px 10px; font-size: 12px;
        }}
        QDateEdit::drop-down {{ border: none; width: 18px; }}
        QDateEdit::down-arrow {{
            image: none; border-left: 4px solid transparent;
            border-right: 4px solid transparent;
            border-top: 6px solid {t['text_dim']};
            width: 0; height: 0; margin-right: 6px;
        }}

        QTextEdit {{
            background-color: {t['lyrics_bg']}; color: {t['lyrics_text']};
            border: 1px solid rgba(255,255,255,25);
            border-radius: 12px; padding: 10px; font-size: 12px;
            selection-background-color: {t['accent']}; selection-color: #ffffff;
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
            background-color: rgba({r},{g},{b},245); color: {t['text']};
            border: 1px solid rgba(255,255,255,25);
            border-radius: 10px; padding: 6px;
        }}
        QMenu::item {{ padding: 8px 22px; border-radius: 6px; }}
        QMenu::item:selected {{ background-color: {t['accent']}; color: #ffffff; }}
        QMenu::separator {{ height: 1px; background: rgba(255,255,255,25); margin: 4px 10px; }}

        QGroupBox {{
            background-color: rgba({r},{g},{b},140);
            border: 1px solid rgba(255,255,255,22);
            border-radius: 12px; margin-top: 14px;
            padding-top: 4px; font-weight: bold; color: {t['accent']};
        }}
        QGroupBox::title {{
            subcontrol-origin: margin; subcontrol-position: top left;
            left: 14px; padding: 0 8px; color: {t['accent']};
        }}

        QToolTip {{
            background-color: {t['accent']}; color: white;
            border: none; border-radius: 6px; padding: 4px 8px;
        }}
        QDialog {{ background-color: rgba({r},{g},{b},245); }}
        QStackedWidget {{ background: transparent; }}
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
        if hasattr(self, "discover_panel"):
            self.discover_panel.apply_theme()

    def _set_theme(self, key):
        if key in THEMES:
            self._theme_name = key
            self.apply_theme(); self.save_config()

    def _open_theme_menu(self):
        menu = QMenu(self)
        for key, t in THEMES.items():
            a = menu.addAction(t["name"])
            a.setCheckable(True); a.setChecked(key == self._theme_name)
            a.triggered.connect(lambda checked=False, k=key: self._set_theme(k))
        menu.addSeparator()
        menu.addAction("⚙  Настройки…", self._open_color_dialog)
        menu.exec(self.theme_btn.mapToGlobal(
            QPoint(0, self.theme_btn.height() + 2)))

    def _open_color_dialog(self):
        ColorSettingsDialog(self).exec()

    def _toggle_reports(self):
        if self.reports_btn.isChecked():
            self.discover_btn.setChecked(False)
            self.stack.setCurrentIndex(1)
            self.reports_panel.refresh()
        else:
            self.stack.setCurrentIndex(0)

    def _close_reports(self):
        self.reports_btn.setChecked(False)
        self.stack.setCurrentIndex(0)

    def _toggle_discover(self, genre=None):
        if self.discover_btn.isChecked():
            self.reports_btn.setChecked(False)
            self.stack.setCurrentIndex(2)
            self.discover_panel.refresh()
            if genre:
                QTimer.singleShot(150, lambda: self._click_genre_chip(genre))
        else:
            self.stack.setCurrentIndex(0)

    def _close_discover(self):
        self.discover_btn.setChecked(False)
        self.stack.setCurrentIndex(0)

    def _click_genre_chip(self, genre):
        for i in range(self.discover_panel.genres_box.count()):
            item = self.discover_panel.genres_box.itemAt(i)
            w = item.widget() if item else None
            if isinstance(w, QPushButton) and genre in w.text().lower():
                w.click(); return

    def _toggle_internet(self):
        self.internet_enabled = not self.internet_enabled
        self._update_net_button(); self.save_config()
        self.status_label.setText(
            "Интернет включён — доступны Genius, Google и Волна"
            if self.internet_enabled
            else "Интернет отключён — сетевые функции скрыты")

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
            self.status_label.setText(f"🎵 Genius: {query}")
        except Exception as e:
            QMessageBox.warning(self, "Ошибка",
                                f"Не удалось открыть браузер:\n{e}")

    def _search_google(self, path):
        name = self._display_name(path)
        if name.lower().endswith((".mp3", ".wav", ".ogg", ".flac", ".m4a")):
            name = os.path.splitext(name)[0]
        artist = self._display_artist(path)
        query = f"{name} {artist}".strip() if artist else name
        try:
            webbrowser.open(f"https://www.google.com/search?q={quote_plus(query)}")
            self.status_label.setText(f"🔍 Google: {query}")
        except Exception as e:
            QMessageBox.warning(self, "Ошибка",
                                f"Не удалось открыть браузер:\n{e}")

    def _get_duration(self, path):
        if path in self._duration_cache:
            return self._duration_cache[path]
        if path.startswith("http://") or path.startswith("https://"):
            self._duration_cache[path] = 0.0; return 0.0
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
        self._duration_base = base_text
        self._duration_idx = 0
        self._duration_total = 0.0
        self.playlist_count.setText(base_text + "  ·  считаю…")
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

    def _build_lyrics_panel(self):
        self.lyrics_panel = QFrame()
        self.lyrics_panel.setObjectName("glassPanel")
        self.lyrics_panel.setMinimumWidth(340)
        self.lyrics_panel.setMaximumWidth(620)

        ll = QVBoxLayout(self.lyrics_panel)
        ll.setContentsMargins(16, 16, 16, 16); ll.setSpacing(8)
        header = QHBoxLayout()
        self.lyrics_title = QLabel("Текст")
        ft = self.lyrics_title.font(); ft.setPointSize(13); ft.setBold(True)
        self.lyrics_title.setFont(ft); self.lyrics_title.setWordWrap(True)
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
        path = None
        if self._playing_path and (self._playing_path.startswith("http://")
                                    or self._playing_path.startswith("https://")):
            path = self._playing_path
        elif 0 <= self.current_index < len(self.playlist):
            path = self.playlist[self.current_index]
        if path is None:
            self.status_label.setText(
                "Нет активного трека — выбери и запусти, затем нажми «Текст»")
            return
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
            screen = QApplication.primaryScreen()
            max_w = 1600
            if screen:
                max_w = min(max_w, screen.availableGeometry().width() - 100)
            if self.width() < max_w:
                self.resize(max_w, self.height())

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

    def _btn(self, text, obj="secondary", fixed=None, size=None, tip=None):
        b = QPushButton(text); b.setObjectName(obj)
        if fixed:
            b.setFixedSize(*fixed)
        f = QFont()
        if obj in ("icon", "like", "play", "net", "liked_btn"):
            f.setFamily("Segoe UI Symbol")
            f.setPointSize(size if size else 11)
            f.setWeight(QFont.Bold); b.setFont(f)
        elif size:
            f.setFamily("Segoe UI"); f.setPointSize(size); b.setFont(f)
        if tip:
            b.setToolTip(tip)
        return b

    def build_ui(self):
        outer = QHBoxLayout(self.central)
        outer.setContentsMargins(0, 0, 0, 0); outer.setSpacing(0)
        outer.addStretch(1)

        content = QWidget()
        content.setMaximumWidth(CONTENT_MAX_WIDTH)
        outer.addWidget(content, 3)

        self._build_lyrics_panel()
        outer.addWidget(self.lyrics_panel, 2)
        self.lyrics_panel.hide()
        outer.addStretch(1)

        root = QVBoxLayout(content)
        root.setContentsMargins(24, 20, 24, 16); root.setSpacing(12)

        header = QWidget()
        hl = QHBoxLayout(header); hl.setContentsMargins(0, 0, 0, 0)
        title = QLabel("♪  Music Player")
        f = title.font(); f.setPointSize(22); f.setBold(True); title.setFont(f)
        hl.addWidget(title)

        hl.addSpacing(12)
        self.reports_btn = self._btn("📊  Отчёты", "secondary")
        self.reports_btn.setFixedHeight(36)
        self.reports_btn.setCheckable(True)
        self.reports_btn.clicked.connect(self._toggle_reports)
        self.reports_btn.setToolTip("Открыть отчёты (встроенная панель)")
        hl.addWidget(self.reports_btn)

        hl.addStretch()

        self.discover_btn = self._btn("🌊  Волна", "secondary")
        self.discover_btn.setFixedHeight(36)
        self.discover_btn.setCheckable(True)
        self.discover_btn.clicked.connect(lambda: self._toggle_discover())
        self.discover_btn.setToolTip("Открыть подбор музыки")
        hl.addWidget(self.discover_btn)

        hl.addSpacing(6)
        self.theme_btn = self._btn(self.theme()["name"], "secondary")
        self.theme_btn.clicked.connect(self._open_theme_menu)
        hl.addWidget(self.theme_btn)

        self.color_btn = self._btn("⚙", "icon", fixed=(42, 38), tip="Настройки")
        self.color_btn.clicked.connect(self._open_color_dialog)
        hl.addWidget(self.color_btn)

        self.net_btn = self._btn("●", "net", fixed=(42, 38),
                                 tip="Интернет включён")
        self.net_btn.clicked.connect(self._toggle_internet)
        hl.addWidget(self.net_btn)

        root.addWidget(header)

        self.now_card = QFrame(); self.now_card.setObjectName("glassPanel")
        nl = QHBoxLayout(self.now_card)
        nl.setContentsMargins(20, 20, 20, 16)
        nl.setSpacing(24)

        self.cover_label = ClickableLabel()
        self.cover_label.setFixedSize(COVER_SIZE, COVER_SIZE)
        self.cover_label.setCursor(Qt.PointingHandCursor)
        self.cover_label.setToolTip("Клик — сменить обложку")
        self.cover_label.clicked.connect(self._cover_menu)
        nl.addWidget(self.cover_label, 0, Qt.AlignTop)

        info = QWidget()
        il = QVBoxLayout(info)
        il.setContentsMargins(0, 0, 0, 0)
        il.setSpacing(6)

        self.now_title = QLabel("—")
        ft = self.now_title.font(); ft.setPointSize(18); ft.setBold(True)
        self.now_title.setFont(ft); self.now_title.setWordWrap(True)
        il.addWidget(self.now_title)

        self.now_artist = QLabel("")
        self.now_artist.setObjectName("dim")
        il.addWidget(self.now_artist)

        il.addSpacing(4)

        now_actions = QHBoxLayout()
        now_actions.setContentsMargins(0, 0, 0, 0)
        now_actions.setSpacing(6)
        self.now_lyrics_btn = self._btn("📄  Текст", "secondary")
        self.now_lyrics_btn.setFixedHeight(28)
        self.now_lyrics_btn.clicked.connect(self._open_current_lyrics)
        self.now_lyrics_btn.setToolTip("Открыть / закрыть текст текущего трека")
        now_actions.addWidget(self.now_lyrics_btn)

        self.now_dna_btn = self._btn("🎯  Похожие", "secondary")
        self.now_dna_btn.setFixedHeight(28)
        self.now_dna_btn.clicked.connect(self._open_current_similar)
        self.now_dna_btn.setToolTip("Найти похожие по звучанию")
        now_actions.addWidget(self.now_dna_btn)
        now_actions.addStretch()
        il.addLayout(now_actions)

        il.addSpacing(6)

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

        nl.addWidget(info, 1)

        right = QWidget()
        rl = QVBoxLayout(right)
        rl.setContentsMargins(0, 0, 0, 0)
        rl.setSpacing(12)

        transport = QHBoxLayout()
        transport.setContentsMargins(0, 0, 0, 0)
        transport.setSpacing(6)
        self.btn_prev = self._btn(G_PREV, "icon", fixed=(48, 44))
        self.btn_prev.clicked.connect(self.prev)
        transport.addWidget(self.btn_prev)
        self.btn_play = self._btn(G_PLAY, "play", fixed=(62, 54))
        self.btn_play.clicked.connect(self.toggle_play)
        transport.addWidget(self.btn_play)
        self.btn_stop = self._btn(G_STOP, "icon", fixed=(48, 44))
        self.btn_stop.clicked.connect(self.stop)
        transport.addWidget(self.btn_stop)
        self.btn_next = self._btn(G_NEXT, "icon", fixed=(48, 44))
        self.btn_next.clicked.connect(self.next)
        transport.addWidget(self.btn_next)
        rl.addLayout(transport)

        vol = QHBoxLayout()
        vol.setContentsMargins(0, 0, 0, 0)
        vol.setSpacing(6)
        vol_icon = QLabel("🔊")
        fv = vol_icon.font(); fv.setPointSize(12); vol_icon.setFont(fv)
        vol.addWidget(vol_icon)

        self.volume_value_label = QLabel(str(self._saved_vol))
        self.volume_value_label.setObjectName("volval")
        self.volume_value_label.setFixedWidth(28)
        self.volume_value_label.setAlignment(Qt.AlignCenter)
        vol.addWidget(self.volume_value_label)

        self.volume_slider = ClickableSlider(Qt.Horizontal)
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setFixedWidth(140)
        self.volume_slider.valueChanged.connect(self._on_volume_change)
        vol.addWidget(self.volume_slider)
        rl.addLayout(vol)

        rl.addStretch()
        nl.addWidget(right, 0)

        root.addWidget(self.now_card)

        self.playlist_controls = QWidget()
        pll = QHBoxLayout(self.playlist_controls)
        pll.setContentsMargins(0, 0, 0, 0); pll.setSpacing(6)

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

        self.btn_new_pl = self._btn("＋", "icon", fixed=(42, 38), tip="Новый")
        self.btn_new_pl.clicked.connect(self._create_playlist)
        pll.addWidget(self.btn_new_pl)

        self.btn_ren_pl = self._btn("✎", "icon", fixed=(42, 38), tip="Переименовать")
        self.btn_ren_pl.clicked.connect(self._rename_playlist)
        pll.addWidget(self.btn_ren_pl)

        self.btn_del_pl = self._btn("✕", "icon", fixed=(42, 38), tip="Удалить")
        self.btn_del_pl.clicked.connect(self._delete_playlist)
        pll.addWidget(self.btn_del_pl)

        pll.addStretch()
        self.playlist_count = QLabel("0 треков")
        self.playlist_count.setObjectName("stats")
        pll.addWidget(self.playlist_count)
        root.addWidget(self.playlist_controls)

        self.search_controls = QWidget()
        srow = QHBoxLayout(self.search_controls)
        srow.setContentsMargins(0, 0, 0, 0); srow.setSpacing(6)

        self.search_scope = QComboBox()
        self.search_scope.addItem("🌐  Везде", "all")
        self.search_scope.addItem("♪  Название", "name")
        self.search_scope.addItem("🎤  Исполнитель", "artist")
        self.search_scope.addItem("🎵  Жанр", "genre")
        self.search_scope.setFixedWidth(160)
        self.search_scope.setToolTip("Область поиска")
        self.search_scope.currentIndexChanged.connect(self._on_search_scope_changed)
        srow.addWidget(self.search_scope)

        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText(
            "🔍 Поиск по названию, исполнителю или жанру…")
        self.search_edit.setClearButtonEnabled(True)
        self.search_edit.textChanged.connect(self._schedule_filter)
        srow.addWidget(self.search_edit, 1)
        root.addWidget(self.search_controls)

        self.stack = QStackedWidget()

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

        self.reports_panel = ReportsPanel(self)
        self.reports_panel.close_requested.connect(self._close_reports)

        self.discover_panel = DiscoverPanel(self)
        self.discover_panel.close_requested.connect(self._close_discover)

        self.stack.addWidget(self.playlist_card)
        self.stack.addWidget(self.reports_panel)
        self.stack.addWidget(self.discover_panel)
        self.stack.currentChanged.connect(self._on_stack_changed)
        root.addWidget(self.stack, 1)

        bottom = QWidget()
        bl = QHBoxLayout(bottom); bl.setContentsMargins(0, 0, 0, 0); bl.setSpacing(6)
        self.btn_files = self._btn("＋  Файлы")
        self.btn_files.clicked.connect(self.add_files); bl.addWidget(self.btn_files)
        self.btn_folder = self._btn("📁  Папка")
        self.btn_folder.clicked.connect(self.add_folder); bl.addWidget(self.btn_folder)
        self.btn_clear = self._btn("Очистить")
        self.btn_clear.clicked.connect(self.clear_playlist); bl.addWidget(self.btn_clear)
        bl.addStretch()
        root.addWidget(bottom)

        self.status_label = QLabel("Ничего не играет")
        self.status_label.setObjectName("dim")
        root.addWidget(self.status_label)

        self.cover_label.setPixmap(self._cover_pixmap(None))

    def _open_playlist_menu(self):
        menu = QMenu(self)
        names = [DEFAULT_LIKED] + [n for n in self.playlists if n != DEFAULT_LIKED]
        for name in names:
            a = menu.addAction(name)
            a.setCheckable(True); a.setChecked(name == self.active_playlist)
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
        is_url = path.startswith("http://") or path.startswith("https://")
        liked = path in self.playlists[DEFAULT_LIKED]
        menu = QMenu(self)
        menu.addAction("▶  Играть", lambda: self.play_index(real_index))
        menu.addAction("✎  Информация о треке…", lambda: self._edit_track_info(path))
        menu.addAction("📄  Текст", lambda: self._open_lyrics(path))
        menu.addAction("🎯  Похожие треки…", lambda: self._open_similar_dialog(path))
        menu.addAction("🖼  Сменить обложку…", lambda: self._change_cover(path))
        menu.addAction("↺  Сбросить оформление", lambda: self._reset_track_meta(path))
        if self.internet_enabled:
            menu.addSeparator()
            if not is_url:
                menu.addAction("🌊  Найти похожее",
                               lambda: self._open_discover_for(path))
            menu.addAction("🎵  Найти на Genius", lambda: self._search_genius(path))
            menu.addAction("🔍  Найти в Google", lambda: self._search_google(path))
        menu.addSeparator()
        menu.addAction(("💔  Убрать из избранного" if liked else "❤  В понравившиеся"),
                       lambda: self._toggle_like(path))
        menu.addSeparator()
        menu.addAction("✕  Удалить из плейлиста", lambda: self._remove_track(real_index))
        menu.exec(global_pos)

    def _open_discover_for(self, path):
        genre = self._display_genre(path).strip().lower()
        self.discover_btn.setChecked(True)
        self._toggle_discover(genre=genre)

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
        menu.addAction("🎯  Похожие треки…", lambda: self._open_similar_dialog(path))
        menu.exec(QCursor.pos())

    def _set_background(self):
        f, _ = QFileDialog.getOpenFileName(
            self, "Выберите фоновое изображение", "",
            "Изображения (*.png *.jpg *.jpeg *.webp *.bmp);;Все файлы (*)")
        if not f:
            return
        self.background_path = f
        self.central.set_background(f); self.save_config()

    def _clear_background(self):
        self.background_path = ""
        self.central.set_background(""); self.save_config()

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
        self.now_title.setText("—"); self.now_artist.setText("")
        self.cover_label.setPixmap(self._cover_pixmap(None))
        self.progress.setRange(0, 0); self.progress.setValue(0)
        self.time_label.setText("0:00 / 0:00")
        if self.stack.currentIndex() != 0:
            self.reports_btn.setChecked(False)
            self.discover_btn.setChecked(False)
            self.stack.setCurrentIndex(0)
        self.save_config()

    def _create_playlist(self):
        name, ok = QInputDialog.getText(self, "Новый плейлист", "Название:")
        if not ok or not name.strip():
            return
        name = name.strip()
        if name == DEFAULT_LIKED:
            QMessageBox.warning(self, "Внимание", "Это имя зарезервировано"); return
        if name in self.playlists:
            QMessageBox.warning(self, "Внимание", "Уже есть"); return
        self.playlists[name] = []; self.save_config(); self._switch_playlist(name)

    def _rename_playlist(self):
        if self.active_playlist == DEFAULT_LIKED:
            QMessageBox.information(self, "Инфо",
                                    "Плейлист «Понравившиеся» переименовать нельзя"); return
        old = self.active_playlist
        new, ok = QInputDialog.getText(self, "Переименовать", "Новое название:", text=old)
        if not ok or not new.strip() or new.strip() == old:
            return
        new = new.strip()
        if new in self.playlists or new == DEFAULT_LIKED:
            QMessageBox.warning(self, "Внимание", "Имя занято"); return
        new_dict = {}
        for k, v in self.playlists.items():
            new_dict[new if k == old else k] = v
        self.playlists = new_dict
        self.active_playlist = new
        self.playlist = self.playlists[new]
        self.playlist_btn.setText(new); self.save_config()

    def _delete_playlist(self):
        if self.active_playlist == DEFAULT_LIKED:
            QMessageBox.information(self, "Инфо",
                                    "Плейлист «Понравившиеся» удалить нельзя"); return
        if len(self.playlists) <= 2:
            QMessageBox.warning(self, "Внимание",
                                "Нельзя удалить последний обычный плейлист"); return
        name = self.active_playlist
        if QMessageBox.question(self, "Удалить",
                                f"Удалить плейлист «{name}»?") != QMessageBox.Yes:
            return
        del self.playlists[name]
        self.active_playlist = next(k for k in self.playlists if k != DEFAULT_LIKED)
        self.playlist = self.playlists[self.active_playlist]
        self.current_index = -1
        self.playlist_btn.setText(self.active_playlist)
        self.search_edit.clear(); self.rebuild_playlist(); self.save_config()

    def _schedule_filter(self):
        self._filter_timer.start()

    def _matches(self, path, query, scope="all"):
        if not query:
            return True
        name   = self._display_name(path).lower()
        artist = self._display_artist(path).lower()
        genre  = self._display_genre(path).lower()
        if scope == "name":
            return query in name
        if scope == "artist":
            return query in artist
        if scope == "genre":
            return query in genre
        return query in name or query in artist or query in genre

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
                w.setParent(None); w.deleteLater()
        self.track_rows = []
        query = self.search_edit.text().strip().lower()
        scope = "all"
        if hasattr(self, "search_scope"):
            scope = self.search_scope.currentData() or "all"

        for real_i, path in enumerate(self.playlist):
            if not self._matches(path, query, scope):
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
            heart_btn.setToolTip("В избранное")
            heart_btn.setFont(self._icon_font(14))
            heart_btn.clicked.connect(lambda _, p=path: self._toggle_like(p))

            self._style_track_row(real_i, name_btn, heart_btn, path)
            h.addWidget(name_btn, 1); h.addWidget(heart_btn, 0)
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
        is_url = path.startswith("http://") or path.startswith("https://")
        prefix = "🌊  " if is_url else ""
        name_btn.setText(f"{prefix}{name}   —   {artist}" if artist else f"{prefix}{name}")
        name_btn.setStyleSheet(self._get_row_style(is_current))
        liked = path in self.playlists[DEFAULT_LIKED]
        heart_btn.setText(G_HEART if liked else G_HEART_EMPTY)
        heart_btn.setProperty("liked", "true" if liked else "false")
        heart_btn.style().unpolish(heart_btn); heart_btn.style().polish(heart_btn)

    def _refresh_highlights(self):
        for real_idx, _, name_btn, heart_btn in self.track_rows:
            if 0 <= real_idx < len(self.playlist):
                self._style_track_row(real_idx, name_btn, heart_btn,
                                      self.playlist[real_idx])

    def _display_name(self, path):
        return self.metadata.get(path, {}).get("display_name") or os.path.basename(path)

    def _display_artist(self, path):
        meta = self.metadata.get(path, {})
        if "artist" in meta:
            return meta["artist"]
        return self._get_tag_from_tags(path, ("TPE1", "artist", "ARTIST", "©ART"))

    def _display_genre(self, path):
        meta = self.metadata.get(path, {})
        if "genre" in meta:
            return meta["genre"]
        return self._get_tag_from_tags(path, ("TCON", "genre", "GENRE", "©gen"))

    def _get_tag_from_tags(self, path, keys):
        if not HAS_MUTAGEN:
            return ""
        if path.startswith("http://") or path.startswith("https://"):
            return ""
        try:
            audio = MutagenFile(path)
            tags = getattr(audio, "tags", None) if audio else None
            if not tags:
                return ""
            for key in keys:
                if key in tags:
                    val = tags[key]
                    if hasattr(val, "text"):
                        return str(val.text[0])
                    return str(val)
        except Exception:
            pass
        return ""

    def _all_genres(self):
        counter = {}
        for path in self.playlist:
            g = self._display_genre(path).strip().lower()
            if not g:
                continue
            for sep in (";", "/", "|"):
                g = g.replace(sep, ",")
            for tag in g.split(","):
                tag = tag.strip()
                if tag:
                    counter[tag] = counter.get(tag, 0) + 1
        return sorted(counter.items(), key=lambda x: -x[1])

    def _edit_track_info(self, path):
        cur_name = self._display_name(path)
        cur_artist = self._display_artist(path)
        cur_genre = self._display_genre(path)
        dlg = TrackInfoDialog(self, cur_name, cur_artist, cur_genre)
        if dlg.exec() != QDialog.Accepted:
            return
        name, artist, genre = dlg.values()
        meta = self.metadata.setdefault(path, {})
        if name: meta["display_name"] = name
        else: meta.pop("display_name", None)
        if artist: meta["artist"] = artist
        else: meta.pop("artist", None)
        if genre: meta["genre"] = genre
        else: meta.pop("genre", None)
        if not meta:
            del self.metadata[path]
        self._invalidate_dna(path)
        self.save_config(); self.rebuild_playlist()
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
            self._invalidate_dna(path)
            self.save_config(); self.rebuild_playlist()
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
            self.stop(); self.current_index = -1
        self.playlist.pop(real_index)
        if real_index < self.current_index:
            self.current_index -= 1
        self.save_config(); self.rebuild_playlist()

    def _toggle_like(self, path):
        liked = self.playlists[DEFAULT_LIKED]
        if path in liked:
            liked.remove(path)
        else:
            liked.append(path)
        self.save_config()
        if self.active_playlist == DEFAULT_LIKED:
            self.rebuild_playlist()

    def _round_pixmap(self, pix, radius):
        out = QPixmap(pix.size())
        out.fill(Qt.transparent)
        p = QPainter(out)
        p.setRenderHint(QPainter.Antialiasing)
        path = QPainterPath()
        path.addRoundedRect(0, 0, pix.width(), pix.height(), radius, radius)
        p.setClipPath(path); p.drawPixmap(0, 0, pix); p.end()
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
        p.setBrush(QBrush(grad)); p.setPen(Qt.NoPen)
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
            if (pix is None or pix.isNull()) and HAS_MUTAGEN \
                    and not path.startswith("http"):
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
        name = self.active_playlist; n = len(self.playlist)
        if n == 0:
            self.status_label.setText("Плейлист уже пуст"); return
        msg = (f"Очистить «{name}»?\n\nБудет удалено треков: {n}.\n"
               f"Файлы на диске останутся, но из плейлиста они исчезнут.")
        if QMessageBox.question(self, "Подтверждение очистки", msg,
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No) != QMessageBox.Yes:
            return
        if self._lyrics_path:
            self._close_lyrics()
        self.stop(); self.playlist.clear(); self.current_index = -1
        self.rebuild_playlist(); self.save_config()
        self.status_label.setText("Плейлист очищен")

    def play_index(self, real_index):
        if 0 <= real_index < len(self.playlist):
            self.current_index = real_index
            self.play_current()

    def play_current(self):
        if not (0 <= self.current_index < len(self.playlist)):
            return
        path = self.playlist[self.current_index]
        is_stream = path.startswith("http://") or path.startswith("https://")
        if not is_stream and not os.path.isfile(path):
            QMessageBox.critical(self, "Ошибка", f"Файл не найден:\n{path}")
            return
        if self._playing_path:
            self._commit_play()
        self._current_duration_ms = 0
        self.spectrum_analyzer.reset()
        if is_stream:
            self.player.setSource(QUrl(path))
        else:
            self.player.setSource(QUrl.fromLocalFile(path))
        self.player.play()
        self.cover_label.setPixmap(self._cover_pixmap(path))
        self.now_title.setText(self._display_name(path))
        self.now_artist.setText(self._display_artist(path))
        prefix = "🌊 Стрим" if is_stream else "Играет"
        self.status_label.setText(f"{prefix}: {self._display_name(path)}")
        self._refresh_highlights()
        self._playing_path = path
        self._play_started_at = time.time()
        if self.lyrics_panel.isVisible() and self._lyrics_path != path:
            self._open_lyrics(path)

    def _play_stream(self, url, title, artist):
        """Играем стрим из «Волны». Теперь тоже пишется в историю."""
        if not url:
            return
        if self._playing_path:
            self._commit_play()
        self._current_duration_ms = 0
        self.spectrum_analyzer.reset()
        if url not in self.metadata:
            self.metadata[url] = {}
        self.metadata[url].setdefault("display_name", title or "—")
        self.metadata[url].setdefault("artist", artist or "Stream")
        try:
            self.player.setSource(QUrl(url))
            self.player.play()
            self.cover_label.setPixmap(self._default_cover())
            self.now_title.setText(title or "—")
            self.now_artist.setText(artist or "Stream")
            self.status_label.setText(f"🌊 Стрим: {title} — {artist}")
            # ← отслеживаем стрим как обычное прослушивание
            self._playing_path = url
            self._play_started_at = time.time()
            if self.lyrics_panel.isVisible() and self._lyrics_path != url:
                self._open_lyrics(url)
        except Exception as e:
            self._log(f"stream play error: {e!r}")
            self.status_label.setText(f"Ошибка стрима: {e}")

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
        self.spectrum_analyzer.reset()
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

    def _on_seek_release(self):
        self._dragging_seek = False
        self.player.setPosition(self.progress.value())

    def _on_seek_move(self, value):
        self.time_label.setText(f"{self._fmt(value)} / {self._fmt(self.player.duration())}")
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
            is_stream = bool(self._playing_path
                             and self._playing_path.startswith("http"))
            if is_stream:
                self.status_label.setText("Стрим завершён")
                if self._playing_path:
                    dur_ms = self.player.duration()
                    if dur_ms <= 0:
                        dur_ms = self._current_duration_ms
                    force = dur_ms / 1000.0 if dur_ms > 0 else None
                    self._commit_play(force_dur=force)
                return
            if not self._advancing:
                self._advancing = True
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
            if self._playing_path and self._playing_path.startswith("http"):
                return
            if 0 <= self.current_index < len(self.playlist):
                self.status_label.setText(
                    f"Играет: {self._display_name(self.playlist[self.current_index])}")
        elif state == QMediaPlayer.PausedState:
            self.status_label.setText("Пауза")
        else:
            if self.status_label.text() not in ("Остановлено", "Ничего не играет",
                                                "Стрим завершён"):
                self.status_label.setText("Остановлено")

    def _on_error(self, err, msg):
        self._log(f"player error: {err} {msg}")
        if err != QMediaPlayer.NoError and msg:
            self.status_label.setText(f"Ошибка: {msg}")

    @staticmethod
    def _icon_font(pt):
        f = QFont("Segoe UI Symbol")
        f.setPointSize(pt); f.setWeight(QFont.Bold)
        return f

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

    def _on_stack_changed(self, index):
        is_playlist = (index == 0)
        if hasattr(self, "playlist_controls"):
            self.playlist_controls.setVisible(is_playlist)
        if hasattr(self, "search_controls"):
            self.search_controls.setVisible(is_playlist)

    def _on_search_scope_changed(self, _idx):
        scope = self.search_scope.currentData() or "all"
        placeholders = {
            "all":    "🔍 Поиск по названию, исполнителю или жанру…",
            "name":   "🔍 Поиск по названию…",
            "artist": "🎤 Поиск по исполнителю…",
            "genre":  "🎵 Поиск по жанру…",
        }
        self.search_edit.setPlaceholderText(placeholders.get(scope, ""))
        self._schedule_filter()

    # ============================================================
    #  🎯 ПОХОЖИЕ ТРЕКИ
    # ============================================================

    @staticmethod
    def _clamp01(x):
        return max(0.0, min(1.0, float(x)))

    @staticmethod
    def _tag_first(tags, keys):
        for k in keys:
            if k in tags:
                val = tags[k]
                if hasattr(val, "text"):
                    return str(val.text[0])
                return str(val)
        return None

    @staticmethod
    def _key_to_num(key_str):
        if not key_str:
            return 0
        s = key_str.strip().upper().replace("♯", "#").replace("♭", "B")
        if len(s) >= 2 and s[:-1].isdigit() and s[-1] in "AB":
            try:
                n = int(s[:-1])
                if 1 <= n <= 12:
                    return n % 12
            except Exception:
                pass
        notes = {"C": 0, "C#": 1, "DB": 1, "D": 2, "D#": 3, "EB": 3,
                 "E": 4, "FB": 4, "F": 5, "F#": 6, "GB": 6, "G": 7,
                 "G#": 8, "AB": 8, "A": 9, "A#": 10, "BB": 10, "B": 11,
                 "CB": 11}
        for suf in ("MINOR", "MAJOR", "MIN", "MAJ", "M"):
            if s.endswith(suf) and len(s) > len(suf):
                s = s[:-len(suf)].rstrip()
                break
        base = s[:2] if len(s) >= 2 and s[1] in "#B" else s[:1]
        return notes.get(base, 0)

    @staticmethod
    def _genre_to_bpm(genre):
        if not genre:
            return 100.0
        g = genre.lower()
        for tag in sorted(GENRE_BPM, key=len, reverse=True):
            if tag in g:
                return float(GENRE_BPM[tag])
        return 100.0

    @staticmethod
    def _genre_to_energy(genre):
        if not genre:
            return 0.5
        g = genre.lower()
        for tag in sorted(GENRE_ENERGY, key=len, reverse=True):
            if tag in g:
                return float(GENRE_ENERGY[tag])
        return 0.5

    def _read_audio_features(self, path, seconds=15):
        if path.startswith("http"):
            return None

        try:
            import soundfile as sf
            import numpy as np
            with sf.SoundFile(path) as f:
                n = int(min(f.samplerate * seconds, len(f)))
                if n < 512:
                    return None
                data = f.read(n, dtype="float32", always_2d=True)
                if data is None or data.size == 0:
                    return None
                mono = data.mean(axis=1)
                rms = float(np.sqrt(np.mean(mono ** 2)))
                signs = np.sign(mono)
                signs[signs == 0] = 1
                zcr = float(np.mean(np.abs(np.diff(signs))) / 2.0)
                return (rms, zcr)
        except Exception:
            pass

        try:
            from pydub import AudioSegment
            import numpy as np
            audio = AudioSegment.from_file(path)
            chunk = audio[:int(seconds * 1000)]
            samples = np.array(chunk.get_array_of_samples(), dtype=np.float32)
            if samples.size < 512:
                return None
            peak = float(np.abs(samples).max())
            if peak > 0:
                samples = samples / peak
            rms = float(np.sqrt(np.mean(samples ** 2)))
            signs = np.sign(samples)
            signs[signs == 0] = 1
            zcr = float(np.mean(np.abs(np.diff(signs))) / 2.0)
            return (rms, zcr)
        except Exception:
            pass

        try:
            import wave, struct
            if not path.lower().endswith((".wav", ".wave")):
                return None
            with wave.open(path, "rb") as w:
                sw = w.getsampwidth()
                nch = w.getnchannels()
                n = min(w.getnframes(), w.getframerate() * seconds)
                raw = w.readframes(n)
                if sw == 2:
                    vals = struct.unpack(f"<{len(raw)//2}h", raw)
                    maxv = 32768.0
                elif sw == 1:
                    vals = struct.unpack(f"<{len(raw)}B", raw)
                    maxv = 128.0
                elif sw == 4:
                    vals = struct.unpack(f"<{len(raw)//4}i", raw)
                    maxv = 2147483648.0
                else:
                    return None
                if nch > 1:
                    vals = vals[::nch]
                if len(vals) < 512:
                    return None
                samples = [v / maxv for v in vals]
                rms = math.sqrt(sum(s * s for s in samples) / len(samples))
                zc = 0
                for i in range(1, len(samples)):
                    if (samples[i] >= 0) != (samples[i - 1] >= 0):
                        zc += 1
                zcr = zc / (2.0 * len(samples))
                return (rms, zcr)
        except Exception:
            pass

        return None

    def _track_dna(self, path):
        mtime = 0.0
        try:
            if not path.startswith("http") and os.path.isfile(path):
                mtime = os.path.getmtime(path)
        except Exception:
            pass
        key = (path, mtime)
        cached = self._dna_cache.get(key)
        if cached is not None:
            return cached

        raw = {
            "bpm": 0.0, "key_num": 0, "key_str": "",
            "energy": 0.5, "zcr": 0.3, "length": 0.0,
            "year": 0, "genre": "", "genre_score": 0.5,
            "has_audio": False,
        }

        if not path.startswith("http") and os.path.isfile(path):
            if HAS_MUTAGEN:
                try:
                    audio = MutagenFile(path)
                    if audio:
                        info = getattr(audio, "info", None)
                        if info:
                            raw["length"] = float(getattr(info, "length", 0) or 0)
                        tags = getattr(audio, "tags", None)
                        if tags:
                            bpm_val = self._tag_first(tags, ("TBPM", "bpm", "BPM"))
                            if bpm_val:
                                try:
                                    raw["bpm"] = float(str(bpm_val).strip().replace(",", "."))
                                except Exception:
                                    pass
                            key_val = self._tag_first(
                                tags, ("TKEY", "key", "KEY", "initialkey", "INITIALKEY"))
                            if key_val:
                                raw["key_str"] = str(key_val).strip()
                                raw["key_num"] = self._key_to_num(raw["key_str"])
                            year_val = self._tag_first(
                                tags, ("TDRC", "TYER", "date", "DATE",
                                       "year", "YEAR", "©day"))
                            if year_val:
                                try:
                                    y = int(str(year_val)[:4])
                                    if 1900 <= y <= 2100:
                                        raw["year"] = y
                                except Exception:
                                    pass
                except Exception:
                    pass

            if raw["year"] == 0:
                try:
                    raw["year"] = datetime.fromtimestamp(mtime).year
                except Exception:
                    pass

            feats = self._read_audio_features(path)
            if feats is not None:
                rms, zcr = feats
                if rms > 0:
                    e = (math.log10(max(rms, 0.0001)) + 3.0) / 2.5
                    raw["energy"] = max(0.0, min(1.0, e))
                else:
                    raw["energy"] = 0.0
                raw["zcr"] = max(0.0, min(1.0, zcr * 2.5))
                raw["has_audio"] = True

        raw["genre"] = self._display_genre(path).strip().lower()
        raw["genre_score"] = self._genre_to_energy(raw["genre"])

        if raw["bpm"] <= 0:
            raw["bpm"] = self._genre_to_bpm(raw["genre"])

        if not raw["has_audio"]:
            raw["energy"] = 0.15 + 0.7 * raw["genre_score"]
            raw["zcr"] = 0.3

        normalized = [
            self._clamp01((raw["bpm"] - 60) / 120.0),
            (raw["key_num"] / 11.0) if raw["key_num"] else 0.5,
            self._clamp01(raw["energy"]),
            self._clamp01(raw["zcr"]),
            self._clamp01((raw["year"] - 1950) / 80.0) if raw["year"] else 0.5,
            self._clamp01(raw["genre_score"]),
        ]
        result = {"raw": raw, "normalized": normalized}
        self._dna_cache[key] = result
        return result

    def _invalidate_dna(self, path):
        keys_to_del = [k for k in self._dna_cache if k[0] == path]
        for k in keys_to_del:
            del self._dna_cache[k]

    @staticmethod
    def _dna_vector(dna):
        r = dna["raw"]
        return (
            r["bpm"] / 180.0,
            (r["key_num"] / 11.0) if r["key_num"] else 0.5,
            r["energy"],
            r["zcr"],
            ((r["year"] - 1950) / 80.0) if r["year"] else 0.5,
            r["genre_score"],
        )

    @staticmethod
    def _weighted_distance(v1, v2):
        weights = (1.2, 0.3, 2.0, 2.0, 0.5, 1.5)
        s = 0.0
        for a, b, w in zip(v1, v2, weights):
            d = a - b
            s += w * d * d
        return math.sqrt(s)

    @staticmethod
    def _similarity_pct(dist):
        if dist < 0.05:
            return 100
        v = 100.0 / (1.0 + math.exp((dist - 1.0) * 1.8))
        return int(round(max(0, min(100, v))))

    def _find_similar_local(self, source_path, limit=20):
        try:
            src = self._track_dna(source_path)
        except Exception:
            return []
        src_vec = self._dna_vector(src)

        candidates = set()
        for pl in self.playlists.values():
            for p in pl:
                if p != source_path:
                    candidates.add(p)
        for p in self.playlist:
            if p != source_path:
                candidates.add(p)

        results = []
        for path in candidates:
            try:
                dna = self._track_dna(path)
                vec = self._dna_vector(dna)
                dist = self._weighted_distance(src_vec, vec)
                pct = self._similarity_pct(dist)
                results.append((path, dist, pct))
            except Exception:
                continue
        results.sort(key=lambda x: x[1])
        return results[:limit]

    def _open_current_similar(self):
        path = None
        if self._playing_path:
            path = self._playing_path
        elif 0 <= self.current_index < len(self.playlist):
            path = self.playlist[self.current_index]
        if not path:
            self.status_label.setText(
                "Нет активного трека — запусти воспроизведение, затем нажми «🎯 Похожие»")
            return
        self._open_similar_dialog(path)

    def _open_similar_dialog(self, path):
        SimilarTracksDialog(self, path).exec()

    def play_path_direct(self, path):
        if path in self.playlist:
            self.play_index(self.playlist.index(path))
            return
        if path.startswith("http://") or path.startswith("https://"):
            self._play_stream(path,
                              self._display_name(path),
                              self._display_artist(path))
            return
        if not os.path.isfile(path):
            return
        self._commit_play()
        self._current_duration_ms = 0
        self.spectrum_analyzer.reset()
        self.player.setSource(QUrl.fromLocalFile(path))
        self.player.play()
        self.cover_label.setPixmap(self._cover_pixmap(path))
        self.now_title.setText(self._display_name(path))
        self.now_artist.setText(self._display_artist(path))
        self.status_label.setText(f"Играет: {self._display_name(path)}")
        self._playing_path = path
        self._play_started_at = time.time()

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