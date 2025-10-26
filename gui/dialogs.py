"""
Dialog ve popup pencereler.

Dosya açma, onay, hata mesajları vb.
"""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QMessageBox, QDialogButtonBox
)
from PySide6.QtCore import Qt
from pathlib import Path
import os
import platform

from gui.styles import Styles


class FileCreatedDialog(QDialog):
    """
    Dosya oluşturuldu dialog'u.
    
    'Dosya başarıyla oluşturuldu. Açmak ister misiniz?' sorusu.
    """
    
    def __init__(self, file_path: str, parent=None):
        """
        FileCreatedDialog başlatıcı.
        
        Args:
            file_path: Oluşturulan dosya yolu
            parent: Parent widget
        """
        super().__init__(parent)
        self.file_path = file_path
        self.result_open = False
        
        self._init_ui()
    
    def _init_ui(self):
        """UI bileşenlerini oluşturur."""
        self.setWindowTitle("Başarılı!")
        self.setModal(True)
        self.setMinimumWidth(400)
        
        layout = QVBoxLayout(self)
        
        # İkon ve mesaj
        icon_label = QLabel("✅")
        icon_label.setStyleSheet("font-size: 48px;")
        icon_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(icon_label)
        
        message = QLabel(f"Dosya başarıyla oluşturuldu:\n\n{Path(self.file_path).name}")
        message.setStyleSheet("font-size: 14px; padding: 10px;")
        message.setAlignment(Qt.AlignCenter)
        message.setWordWrap(True)
        layout.addWidget(message)
        
        question = QLabel("Dosyayı açmak ister misiniz?")
        question.setStyleSheet("font-size: 13px; font-weight: bold; padding: 10px;")
        question.setAlignment(Qt.AlignCenter)
        layout.addWidget(question)
        
        # Butonlar
        button_layout = QHBoxLayout()
        
        open_btn = QPushButton("📂 Aç")
        open_btn.setStyleSheet(Styles.SUCCESS_BUTTON)
        open_btn.clicked.connect(self._on_open)
        button_layout.addWidget(open_btn)
        
        close_btn = QPushButton("Kapat")
        close_btn.setStyleSheet(Styles.SECONDARY_BUTTON)
        close_btn.clicked.connect(self.reject)
        button_layout.addWidget(close_btn)
        
        layout.addLayout(button_layout)
    
    def _on_open(self):
        """Dosyayı aç."""
        self.result_open = True
        self.accept()


class ConfirmDialog(QDialog):
    """
    Onay dialog'u.
    
    Kullanıcıdan onay ister (Evet/Hayır).
    """
    
    def __init__(self, title: str, message: str, parent=None):
        """
        ConfirmDialog başlatıcı.
        
        Args:
            title: Dialog başlığı
            message: Onay mesajı
            parent: Parent widget
        """
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setModal(True)
        
        layout = QVBoxLayout(self)
        
        # Mesaj
        msg_label = QLabel(message)
        msg_label.setStyleSheet("font-size: 13px; padding: 20px;")
        msg_label.setWordWrap(True)
        layout.addWidget(msg_label)
        
        # Butonlar
        buttons = QDialogButtonBox(
            QDialogButtonBox.Yes | QDialogButtonBox.No
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)


class ConflictDialog(QDialog):
    """
    Dosya çakışması dialog'u.
    
    Dosya zaten varsa: Üzerine yaz / Tarih ekle / İptal
    """
    
    OVERWRITE = 1
    ADD_DATE = 2
    CANCEL = 3
    
    def __init__(self, file_path: str, parent=None):
        """
        ConflictDialog başlatıcı.
        
        Args:
            file_path: Çakışan dosya yolu
            parent: Parent widget
        """
        super().__init__(parent)
        self.file_path = file_path
        self.user_choice = self.CANCEL
        
        self._init_ui()
    
    def _init_ui(self):
        """UI bileşenlerini oluşturur."""
        self.setWindowTitle("Dosya Zaten Mevcut")
        self.setModal(True)
        self.setMinimumWidth(450)
        
        layout = QVBoxLayout(self)
        
        # Uyarı ikonu
        icon_label = QLabel("⚠️")
        icon_label.setStyleSheet("font-size: 48px;")
        icon_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(icon_label)
        
        # Mesaj
        message = QLabel(
            f"Bu isimde bir dosya zaten mevcut:\n\n"
            f"{Path(self.file_path).name}\n\n"
            f"Ne yapmak istersiniz?"
        )
        message.setStyleSheet("font-size: 13px; padding: 10px;")
        message.setAlignment(Qt.AlignCenter)
        message.setWordWrap(True)
        layout.addWidget(message)
        
        # Butonlar
        overwrite_btn = QPushButton("🔄 Üzerine Yaz")
        overwrite_btn.setStyleSheet(Styles.DANGER_BUTTON)
        overwrite_btn.clicked.connect(self._on_overwrite)
        layout.addWidget(overwrite_btn)
        
        add_date_btn = QPushButton("📅 Tarih Ekle")
        add_date_btn.setStyleSheet(Styles.PRIMARY_BUTTON)
        add_date_btn.clicked.connect(self._on_add_date)
        layout.addWidget(add_date_btn)
        
        cancel_btn = QPushButton("❌ İptal")
        cancel_btn.setStyleSheet(Styles.SECONDARY_BUTTON)
        cancel_btn.clicked.connect(self._on_cancel)
        layout.addWidget(cancel_btn)
    
    def _on_overwrite(self):
        """Üzerine yaz seçeneği."""
        self.user_choice = self.OVERWRITE
        self.accept()
    
    def _on_add_date(self):
        """Tarih ekle seçeneği."""
        self.user_choice = self.ADD_DATE
        self.accept()
    
    def _on_cancel(self):
        """İptal seçeneği."""
        self.user_choice = self.CANCEL
        self.reject()


def show_info(parent, title: str, message: str):
    """
    Bilgi mesajı gösterir.
    
    Args:
        parent: Parent widget
        title: Başlık
        message: Mesaj
    """
    QMessageBox.information(parent, title, message)


def show_warning(parent, title: str, message: str):
    """
    Uyarı mesajı gösterir.
    
    Args:
        parent: Parent widget
        title: Başlık
        message: Mesaj
    """
    QMessageBox.warning(parent, title, message)


def show_error(parent, title: str, message: str):
    """
    Hata mesajı gösterir.
    
    Args:
        parent: Parent widget
        title: Başlık
        message: Mesaj
    """
    QMessageBox.critical(parent, title, message)


def show_file_created(parent, file_path: str) -> bool:
    """
    Dosya oluşturuldu dialog'unu gösterir.
    
    Args:
        parent: Parent widget
        file_path: Dosya yolu
        
    Returns:
        Kullanıcı 'Aç' butonuna bastı mı?
    """
    dialog = FileCreatedDialog(file_path, parent)
    dialog.exec()
    return dialog.result_open


def open_file_location(file_path: str):
    """
    Dosyanın bulunduğu klasörü açar ve dosyayı seçer.
    
    Args:
        file_path: Dosya yolu
    """
    path = Path(file_path)
    
    if not path.exists():
        return
    
    system = platform.system()
    
    try:
        if system == "Windows":
            # Windows: Explorer'da dosyayı seç
            os.startfile(path.parent)
        elif system == "Darwin":
            # macOS: Finder'da dosyayı seç
            os.system(f'open -R "{path}"')
        else:
            # Linux: Dosya yöneticisinde klasörü aç
            os.system(f'xdg-open "{path.parent}"')
    except Exception:
        # Hata durumunda sadece klasörü aç
        try:
            if system == "Windows":
                os.startfile(path.parent)
            else:
                os.system(f'xdg-open "{path.parent}"')
        except Exception:
            pass


def open_file(file_path: str):
    """
    Dosyayı varsayılan programla açar.
    
    Args:
        file_path: Dosya yolu
    """
    path = Path(file_path)
    
    if not path.exists():
        return
    
    system = platform.system()
    
    try:
        if system == "Windows":
            os.startfile(path)
        elif system == "Darwin":
            os.system(f'open "{path}"')
        else:
            os.system(f'xdg-open "{path}"')
    except Exception:
        pass