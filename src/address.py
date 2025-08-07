from PySide6.QtCore import (
    QSize, Qt
)
from PySide6.QtGui import (
    QFont, QIcon, QColor, QBrush
)
from PySide6.QtWidgets import (
    QFrame,QHBoxLayout, QListWidget,
    QListWidgetItem, QPushButton,
    QSizePolicy, QVBoxLayout, QWidget, QAbstractItemView
)

from change import Change
from tkinter import messagebox
from email_validator import validate_email

class Address:
    """
    Gerencia a interface e as operações relacionadas aos endereços de email de uma empresa.
    Permite adicionar, editar, remover e validar emails, além de controlar as alterações para persistência.
    """

    def __init__(self, id, address):
        """
        Inicializa o widget de emails com os dados fornecidos.
        Args:
            id (list): Lista de IDs dos emails.
            address (list): Lista de endereços de email.
        """
        self.sizePolicy = QSizePolicy(
            QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Maximum
        )
        self.sizePolicy_2 = QSizePolicy(
            QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Expanding
        )
        
        self.sizePolicy.setHorizontalStretch(0)
        self.sizePolicy.setVerticalStretch(0)

        self.font = QFont()
        self.font.setFamilies([u"Tw Cen MT"])
        self.font.setPointSize(12)

        self.font2 = QFont()
        self.font2.setFamilies([u"Tw Cen MT"])
        self.font2.setPointSize(16)

        self.add_brush = QBrush(QColor(179, 255, 178, 255))
        self.add_brush.setStyle(Qt.BrushStyle.Dense1Pattern)

        self.updt_brush = QBrush(QColor(189, 253, 254, 255))
        self.updt_brush.setStyle(Qt.BrushStyle.Dense1Pattern)

        self.remove_brush = QBrush(QColor(254, 139, 139, 255))
        self.remove_brush.setStyle(Qt.BrushStyle.Dense1Pattern)

        self.no_brush = QBrush(Qt.BrushStyle.NoBrush)

        self.send_btn, self.page = self.__page()
        
        self.valid_email_pattern = r'@|\.com|\.org'
        self.fill(id, address)
        pass

    def __call__(self, *args, **kwds):
        """
        Retorna o botão de envio e o widget da página de emails.
        """
        return self.send_btn, self.page

    def __page(self):
        """
        Cria a página de emails com lista, botões e botão de próximo.
        """
        page_2 = QWidget()
        verticalLayout = QVBoxLayout(page_2)

        self.listWidget_email = self.__list(page_2)
        self.listWidget_email.setStyleSheet(u"background-color: rgb(255, 255, 255);")
        verticalLayout.addWidget(self.listWidget_email, alignment= Qt.AlignmentFlag.AlignCenter)

        frame_email_func = QFrame(page_2)
        frame_email_func.setFrameShape(QFrame.Shape.StyledPanel)
        frame_email_func.setFrameShadow(QFrame.Shadow.Raised)
        horizontalLayout = QHBoxLayout(frame_email_func)

        pushButton_add, pushButton_remove = self.__buttons(frame_email_func)
        horizontalLayout.addWidget(pushButton_add)
        horizontalLayout.addWidget(pushButton_remove)

        verticalLayout.addWidget(frame_email_func)

        pushButton_send_email = QPushButton(page_2)
        pushButton_send_email.setText('Próximo  ')
        pushButton_send_email.setStyleSheet(
            u"background-color: rgb(255, 255, 255);\n"
            "border: 1px solid rgb(85, 170, 255);\n"
            "padding: 5px;\n"
            "border-radius: 8px;"
        )
        pushButton_send_email.setFont(self.font2)
        pushButton_send_email.setIcon(
            QIcon(QIcon.fromTheme(QIcon.ThemeIcon.MediaSkipForward))
        )
        pushButton_send_email.setLayoutDirection(
            Qt.LayoutDirection.RightToLeft
        )
        verticalLayout.addWidget(pushButton_send_email)
        return pushButton_send_email, page_2

    def __buttons(self, frame_email_func):
        """
        Cria os botões de adicionar e remover email.
        """
        pushButton_add = QPushButton(frame_email_func)
        icon = QIcon(QIcon.fromTheme(QIcon.ThemeIcon.ListAdd))
        pushButton_add.setIcon(icon)
        pushButton_add.setStyleSheet(u"background-color: rgb(235, 235, 235);")
        pushButton_add.clicked.connect(self.add)

        pushButton_remove = QPushButton(frame_email_func)
        icon_2 = QIcon(QIcon.fromTheme(QIcon.ThemeIcon.ListRemove))
        pushButton_remove.setIcon(icon_2)
        pushButton_remove.setStyleSheet(u"background-color: rgb(235, 235, 235);")
        pushButton_remove.clicked.connect(self.remove)
        return pushButton_add, pushButton_remove

    def __list(self, page_2):
        """
        Cria o QListWidget para exibir os emails.
        """
        listWidget_email = QListWidget(page_2)
        
        self.sizePolicy_2.setHeightForWidth(
            listWidget_email.sizePolicy().hasHeightForWidth()
        )
        listWidget_email.setSizePolicy(self.sizePolicy_2)
        
        listWidget_email.setFont(self.font)

        listWidget_email.itemChanged.connect(self.updt)
        return listWidget_email

    def fill(self, ids, data):
        """
        Preenche a lista de emails com os dados fornecidos.
        """
        self.listWidget_email.clear()
        for row, value in enumerate(data):
            item = QListWidgetItem()
            item.setFlags(Qt.ItemIsSelectable |Qt.ItemIsEditable |Qt.ItemIsEnabled)
            item.__setattr__('id', ids[row])
            item.__setattr__('edited', False)
            item.__setattr__('not_updatable', False)
            item.setText(str(value))
            self.listWidget_email.addItem(item)

    def add(self):
        """
        Adiciona um novo campo de email para edição.
        """
        item = QListWidgetItem()
        item.setFlags(Qt.ItemIsSelectable |Qt.ItemIsEditable |Qt.ItemIsEnabled)
        item.__setattr__('id', None)
        item.__setattr__('edited', False)
        item.__setattr__('not_updatable', False)
        item.setBackground(self.add_brush)

        self.listWidget_email.addItem(item)
        self.listWidget_email.openPersistentEditor(item)
        self.listWidget_email.editItem(item)
        item.setSelected(True)

    def updt(self):
        """
        Atualiza o estado visual do item selecionado após edição.
        """
        item = self.listWidget_email.selectedItems()[0]
        if item.__getattribute__('not_updatable') == True:
            item.__setattr__('not_updatable', False)
            return 
        
        self.listWidget_email.closePersistentEditor(item)
        bush = self.add_brush\
                if None == item.__getattribute__('id')\
                    else self.updt_brush
        item.__setattr__('edited', True)
        item.setBackground(bush)

    def remove(self):
        """
        Marca ou remove um email da lista, conforme o contexto.
        """
        try:
            item = self.listWidget_email.selectedItems()[0]
            if item.text() == '' or item.__getattribute__('id') == None:
                    self.listWidget_email.takeItem(
                        self.listWidget_email.row(item)
                    )
            else:
                bush = self.remove_brush
                if item.background() == self.remove_brush:
                    bush = self.updt_brush\
                        if True == item.__getattribute__('edited')\
                            else self.no_brush
                item.__setattr__('not_updatable', True)
                item.setBackground(bush)
        except IndexError:
            messagebox.showerror('Aviso', 'Primeiro, selecione o e-mail que deseja remover')

    def change(self) -> Change | None:
        """
        Retorna um objeto Change com as alterações feitas nos emails.
        """
        if self.has_change() == False:
            return None
        
        changes = Change()
        for row in range(self.listWidget_email.count()):
            item = self.listWidget_email.item(row)
            brush = item.background()
            if brush == self.add_brush:
                text = item.text()
                self.__valid_add(text)
                changes.to_add(text)

            elif brush == self.updt_brush:
                changes.to_updt(
                    item.__getattribute__('id'), 
                    item.text()
                )

            elif brush == self.remove_brush:
                changes.to_remove(item.__getattribute__('id'))
        return changes
    
    def has_change(self)-> bool:
        """
        Verifica se há alterações pendentes nos emails.
        """
        for row in range(self.listWidget_email.count()):
            item = self.listWidget_email.item(row)
            if item.background() != self.no_brush:
                return True
        return False

    def __valid_add(self, text):
        """
        Valida o formato do email antes de adicionar.
        """
        if text == '':
            raise Exception(
                    'Defina um endereço de e-mail para o espaço adcionado, caso contrário, o remova'
            )
                    
        validate_email(text)
                
    def save(self):
        """
        Aplica as alterações visuais e remove emails marcados para remoção.
        """
        remove_count = 0
        for row in range(self.listWidget_email.count()):
            current_row = row - remove_count
            item = self.listWidget_email.item(current_row)
            brush = item.background()
            if brush == self.remove_brush:
                self.listWidget_email.takeItem(current_row)
                remove_count = remove_count + 1
            elif brush in [self.add_brush, self.updt_brush]:
                item.__setattr__('not_updatable', True)
                item.setBackground(self.no_brush)

    def data(self) -> list[str]:
        """
        Retorna a lista atual de emails.
        """
        data_row = []
        for row in range(self.listWidget_email.count()):
            item = self.listWidget_email.item(row)
            data_row.append(item.text())
        return data_row