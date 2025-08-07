from PySide6.QtWidgets import (
    QMainWindow, QApplication, QListWidgetItem, QAbstractItemView
)
from PySide6.QtGui import (
    QIcon, QMovie
)

from PySide6.QtCore import (
    QThread, QDate
)

from dateutil.relativedelta import relativedelta
from local_changes import LocalChanges
from window_pend import Ui_MainWindow
from re import compile, findall
from tkinter import messagebox
from database import Database 
from datetime import datetime
from pendency import Pedency
from address import Address
from postman import Postman
from startfile import startfile
from pathlib import Path
from sheet import Sheet
from pymysql import err
from email_validator import EmailNotValidError
import sys

class MainWindow(QMainWindow, Ui_MainWindow):
    """
    Classe principal da aplicação. Gerencia a interface gráfica, interações do usuário, integração com banco de dados, controle de empresas, pendências, impostos, emails, geração de relatórios e envio de emails.
    """
    icon_path = Path(__file__).parent / 'imgs' / '{0}_icon.png'
    current_companie_id = ''

    def __init__(self, parent = None) -> None:
        """
        Inicializa a janela principal, configura conexões, ícones, widgets e carrega dados iniciais.
        """
        super().__init__(parent)
        self.message_error_docker = 'Falha na conexão com o banco de dados. Favor verificar se o aplicativo "DOCKER" está inicializado no servidor, caso constrário, entre em contato com o suporte disponível\n\n{}'

        self.db = self.try_conection()
        self.setupUi(self)

        self.setWindowIcon(
            QIcon(
                (Path(__file__).parent / 'imgs' / 'GerenPedenContab.ico').__str__())
        )

        self.message_select = 'Primeiro, clique 1 vez na empresa que deseja {0}'
        self.message_remove = 'Confirma a remoção desta empresa?\nTodas suas pendências e emails cadastrados também serão excluídos'
        self.message_save = 'Tem certeza que deseja salvar estas alterações?'
        self.message_pending_save = 'Antes de recarregar os dados, faça ou cancele o salvamento das alterações pendentes'
        self.message_no_save = 'Não há alterações a serem salvas'
        self.message_exit_save = 'Tem certeza que deseja sair da empresa SEM SALVAR as mudanças feitas nela?\n\nCaso não queira PERDER as alterações, selecione "não" e as salve'
        self.message_send_email = 'Confirma o envio dessas pendências aos emails cadastrados?'

        self.__init_date_sheet()

        self.local_changes = LocalChanges()
        sender_name = self.local_changes.sender_name()
        self.lineEdit_name_func.setText(sender_name)

        self.connections = {}
        self.enable_status = True

        self.ref_universal = {
            'companies': [
                {
                    self.pushButton_add_func: self.add_companie,
                    self.pushButton_remove_func: self.remove_companie,
                    self.pushButton_edit_func: self.edit_companie,
                    self.pushButton_reload_companie: self.__fill_companies,
                    self.pushButton_confirm_operation: self.confirm_companie,
                    self.pushButton_cancel_operation: self.cancel_companie
                },
                {
                    self.pushButton_add_func: 'Adciona empresa a lista de empresas cadastradas',
                    self.pushButton_remove_func: 'Remove empresa cadastrada',
                    self.pushButton_edit_func: 'Edita o nome de empresa cadastrada',
                    self.pushButton_sheet_func: 'Gera relatório de envio de todas empresas cadastradas',
                }
            ],
            'pending': [
                {
                    self.pushButton_reload_companie: self.reload_pedency,
                },
                {
                    self.pushButton_add_func: 'Adciona pendência contábil a empresa selecionada',
                    self.pushButton_remove_func: 'Remove a pendência contábil selecionada com 1 clique',
                    self.pushButton_edit_func: 'Edita a pendência contábil selecionada com 1 clique',
                    self.pushButton_sheet_func: 'Gera relatório de envios exclusivo da empresa atual',
                }
            ],
            'taxes': [
                {
                    self.pushButton_add_func: self.add_taxes,
                    self.pushButton_remove_func: self.remove_taxes,
                    self.pushButton_edit_func: self.edit_taxes,
                    self.pushButton_reload_companie: self.__fill_taxes,
                    self.pushButton_confirm_operation: self.confirm_taxes,
                    self.pushButton_cancel_operation: self.cancel_taxes
                },
                {
                    self.pushButton_add_func: 'Adciona imposto a lista de impostos cadastrados',
                    self.pushButton_remove_func: 'Remove imposto cadastrado',
                    self.pushButton_edit_func: 'Edita o nome de imposto cadastrado',
                }
            ]
        }

        self.ref_disable_btns = [
            self.pushButton_add_func,
            self.pushButton_remove_func,
            self.pushButton_edit_func,
            self.pushButton_save_func,
            self.pushButton_send_email,
            self.pushButton_sheet_func,
            self.pushButton_exit_companie,
            self.pushButton_reload_companie,
            self.pushButton_taxes,
            self.pushButton_companies
        ]

        self.ref_date_sheet = [self.dateEdit_from, self.dateEdit_until]

        self.movie = QMovie(
            (Path(__file__).parent / 'imgs' / 'load.gif').__str__()
        )
        self.label_load_gif.setMovie(self.movie)

        self.open_pedency_connection = None
        self.re_connect_pedency()
        self.frame_operation.setHidden(True)

        self.__fill_companies()
        self.__fill_taxes()
        self.__init_icons()
        self.switch_focus('companies')

        self.pushButton_companies.clicked.connect(self.open_taxes)
        self.pushButton_taxes.clicked.connect(self.exit_taxes)

        self.pushButton_cancel_email.clicked.connect(self.exit_assign)
        self.pushButton_send_email.clicked.connect(self.send_email)
        self.pushButton_save_func.clicked.connect(self.save)
        self.pushButton_exit_companie.clicked.connect(self.exit_pedency)
        self.pushButton_sheet_func.clicked.connect(self.sheet)
        self.pushButton_save_func.setHidden(True)

        self.pushButton_add_func.clicked.connect(self.in_operation)
        self.pushButton_edit_func.clicked.connect(self.in_operation)
        self.pushButton_cancel_operation.clicked.connect(self.in_operation)
        self.pushButton_confirm_operation.clicked.connect(self.in_operation)

    def re_connect_pedency(self):
        """
        (Re)conecta o evento de duplo clique na lista de empresas para abrir as pendências.
        """
        """
        (Re)conecta o evento de duplo clique na lista de empresas para abrir as pendências.
        """
        if self.open_pedency_connection == None:
            self.open_pedency_connection = self.listWidget_companie\
                .itemDoubleClicked.connect(self.open_pedency)
        else:
            self.listWidget_companie.disconnect(self.open_pedency_connection)
            self.open_pedency_connection = None

    def in_operation(self):
        """
        Alterna o estado de operação, desabilitando botões e mostrando/escondendo o frame de operação.
        """
        """
        Alterna o estado de operação, desabilitando botões e mostrando/escondendo o frame de operação.
        """
        self.disable_btns()
        hide = not self.frame_operation.isHidden()
        self.frame_operation.setHidden(hide)

    def try_conection(self):
        """
        Tenta conectar ao banco de dados, exibindo mensagem de erro caso falhe.
        """
        """
        Tenta conectar ao banco de dados, exibindo mensagem de erro caso falhe.
        """
        try:
            return Database()
        except err.OperationalError as e:
            messagebox.showerror('Aviso!', self.message_error_docker.format(e))
            sys.exit()

    def __init_date_sheet(self):
        """
        Inicializa os campos de data do relatório com datas padrão (último mês).
        """
        """
        Inicializa os campos de data do relatório com datas padrão (último mês).
        """
        now = datetime.now()
        regex = compile(r'[0-9]+')
        ref = {
            self.dateEdit_until: now,
            self.dateEdit_from: now - relativedelta(months = 1)
        }

        for widget, date in ref.items():
            list_date = findall(regex, date.strftime('%d/%m/%Y'))
            d, m, y = list_date
            date = QDate(int(y), int(m), int(d))
            widget.setDate(date)

    def __init_icons(self):
        """
        Inicializa ícones dos botões principais.
        """
        """
        Inicializa ícones dos botões principais.
        """
        icon_ref ={
            self.pushButton_add_func: 'add',
            self.pushButton_remove_func: 'remove'
        }
        for btn, icon_type in icon_ref.items():
            icon = QIcon()
            icon.addFile(str(self.icon_path).format(icon_type))
            btn.setIcon(icon)

    def __fill_companies(self):
        """
        Preenche a lista de empresas cadastradas a partir do banco de dados.
        """
        """
        Preenche a lista de empresas cadastradas a partir do banco de dados.
        """
        data = self.db.companies()
        self.listWidget_companie.clear()
        for id, name in data.items():
            item = QListWidgetItem()
            item.setText(name)
            item.__setattr__('id', id)
            self.listWidget_companie.addItem(item)

    def __fill_taxes(self):
        """
        Preenche a lista de impostos cadastrados a partir do banco de dados.
        """
        """
        Preenche a lista de impostos cadastrados a partir do banco de dados.
        """
        data = self.db.taxes()
        self.listWidget_taxes.clear()
        for id, name in data.items():
            item = QListWidgetItem()
            item.setText(name)
            item.__setattr__('id', id)
            self.listWidget_taxes.addItem(item)

    def add_companie(self):
        """
        Adiciona uma nova empresa à lista para edição.
        """
        """
        Adiciona uma nova empresa à lista para edição.
        """
        item = QListWidgetItem()
        item.setText('Nome da empresa')
        item.__setattr__('id', None)

        self.re_connect_pedency()

        self.current_item_edited = item
        self.listWidget_companie.addItem(item)
        self.listWidget_companie.openPersistentEditor(item)
        self.listWidget_companie.editItem(item)

    def add_taxes(self):
        """
        Adiciona um novo imposto à lista para edição.
        """
        """
        Adiciona um novo imposto à lista para edição.
        """
        item = QListWidgetItem()
        item.setText('Nome do imposto')
        item.__setattr__('id', None)

        self.current_item_edited = item
        self.listWidget_taxes.addItem(item)
        self.listWidget_taxes.openPersistentEditor(item)
        self.listWidget_taxes.editItem(item)

    def edit_companie(self):
        """
        Permite editar o nome da empresa selecionada.
        """
        """
        Permite editar o nome da empresa selecionada.
        """
        try:
            item = self.listWidget_companie.selectedItems()[0]
            self.re_connect_pedency()

            self.current_old_edited = item.text()
            self.current_item_edited = item
            self.listWidget_companie.openPersistentEditor(item)
            self.listWidget_companie.editItem(item)

        except IndexError:
            messagebox.showerror('Aviso', self.message_select.format('editar'))
        except Exception as error: 
            messagebox.showwarning('Aviso', error)

    def edit_taxes(self):
        """
        Permite editar o nome do imposto selecionado.
        """
        """
        Permite editar o nome do imposto selecionado.
        """
        try:
            item = self.listWidget_taxes.selectedItems()[0]

            self.current_old_edited = item.text()
            self.current_item_edited = item
            self.listWidget_taxes.openPersistentEditor(item)
            self.listWidget_taxes.editItem(item)

        except IndexError:
            messagebox.showerror('Aviso', self.message_select.format('editar'))
        except Exception as error: 
            messagebox.showwarning('Aviso', error)

    def confirm_companie(self):
        """
        Confirma a adição ou edição de uma empresa.
        """
        """
        Confirma a adição ou edição de uma empresa.
        """
        try:
            item = self.current_item_edited
            name = item.text()
            if name == '':
                raise Exception('Nome de empresa inválida')
            
            self.listWidget_companie.closePersistentEditor(item)

            id = item.__getattribute__('id')
            if id == None:
                id = self.db.add_companie(name)
                item.__setattr__('id', id)
            else:
                self.db.edit_companie(id, name)

            self.re_connect_pedency()
        except Exception as error:
            messagebox.showwarning('Aviso', error)

    def cancel_companie(self):
        """
        Cancela a edição ou adição de uma empresa.
        """
        """
        Cancela a edição ou adição de uma empresa.
        """
        item = self.current_item_edited
        self.listWidget_companie.closePersistentEditor(item)

        if item.__getattribute__('id') == None:
            self.listWidget_companie.takeItem(
                self.listWidget_companie.row(item)
            )
        else:
            item.setText(self.current_old_edited)

        self.re_connect_pedency()

    def cancel_taxes(self):
        """
        Cancela a edição ou adição de um imposto.
        """
        """
        Cancela a edição ou adição de um imposto.
        """
        item = self.current_item_edited
        self.listWidget_taxes.closePersistentEditor(item)

        if item.__getattribute__('id') == None:
            self.listWidget_taxes.takeItem(
                self.listWidget_taxes.row(item)
            )
        else:
            item.setText(self.current_old_edited)

    def confirm_taxes(self):
        """
        Confirma a adição ou edição de um imposto.
        """
        """
        Confirma a adição ou edição de um imposto.
        """
        try:
            item = self.current_item_edited
            name = item.text()
            if name == '':
                raise Exception('Nome do imposto inválido')
            
            self.listWidget_taxes.closePersistentEditor(item)

            id = item.__getattribute__('id')
            if id == None:
                id = self.db.add_taxes(name)
                item.__setattr__('id', id)
            else:
                self.db.edit_taxes(id, name)

        except Exception as error:
            messagebox.showwarning('Aviso', error)

    def remove_companie(self):
        """
        Remove a empresa selecionada, após confirmação do usuário.
        """
        """
        Remove a empresa selecionada, após confirmação do usuário.
        """
        try:
            self.disable_btns()
            items = self.listWidget_companie.selectedItems()
            if len(items) == 0:
                raise Exception(self.message_select.format('remover'))
            
            if messagebox.askyesno('Aviso', self.message_remove) == False:
                self.disable_btns()
                return None
            
            item = items[0]
            self.db.remove_companie(item.__getattribute__('id'))
            self.listWidget_companie.takeItem(
                self.listWidget_companie.row(item)
            )
            self.disable_btns()
        except Exception as error:
            messagebox.showwarning('Aviso', error)
            self.disable_btns()

    def remove_taxes(self):
        """
        Remove o imposto selecionado, após confirmação do usuário.
        """
        """
        Remove o imposto selecionado, após confirmação do usuário.
        """
        try:
            self.disable_btns()
            items = self.listWidget_taxes.selectedItems()
            if len(items) == 0:
                raise Exception(self.message_select.format('remover'))
            
            if messagebox.askyesno('Aviso', self.message_remove) == False:
                return None
            
            item = items[0]
            self.db.remove_taxes(item.__getattribute__('id'))
            self.listWidget_taxes.takeItem(
                self.listWidget_taxes.row(item)
            )
            self.disable_btns()
        except Exception as error:
            self.disable_btns()
            messagebox.showwarning('Aviso', error)

    def open_taxes(self):
        """
        Abre a tela de impostos.
        """
        """
        Abre a tela de impostos.
        """
        self.stackedWidget_companie.setCurrentIndex(1)
        self.pushButton_sheet_func.setEnabled(False)
        self.switch_focus('taxes')

    def exit_taxes(self):
        """
        Retorna à tela de empresas.
        """
        """
        Retorna à tela de empresas.
        """
        self.stackedWidget_companie.setCurrentIndex(0)
        self.pushButton_sheet_func.setEnabled(True)
        self.switch_focus('companies')

    def open_pedency(self):
        """
        Abre a tela de pendências da empresa selecionada.
        """
        """
        Abre a tela de pendências da empresa selecionada.
        """
        self.switch_focus('pending')
        item = self.listWidget_companie.selectedItems()[0]
        self.label_current_companie.setText(item.text())
        self.current_companie_id = item.__getattribute__('id')

        self.pedency = self.__pedency(self.current_companie_id)
        self.address = Address(*self.db.emails(self.current_companie_id))

        next_btn, page = self.address()
        next_btn.clicked.connect(self.open_assign)
        self.stackedWidget_email.addWidget(page)

        self.pushButton_save_func.setHidden(False)
        self.pushButton_edit_func.setHidden(True)
        self.stackedWidget_companie.setCurrentIndex(2)
        self.stackedWidget_email.setCurrentIndex(2)

    def __pedency(self, id):
        """
        Inicializa o widget de pendências para a empresa selecionada.
        """
        """
        Inicializa o widget de pendências para a empresa selecionada.
        """
        pedency = Pedency(*self.db.pedency(id))

        self.connections[self.pushButton_add_func] =\
            self.pushButton_add_func.clicked.connect(
                lambda: pedency.add()
            )

        self.connections[self.pushButton_remove_func] =\
            self.pushButton_remove_func.clicked.connect(
                lambda: pedency.remove()
            )
        
        self.connections[self.pushButton_cancel_operation] =\
            self.pushButton_cancel_operation.clicked.connect(
                lambda: pedency.cancel()
            )
        
        self.connections[self.pushButton_confirm_operation] =\
            self.pushButton_confirm_operation.clicked.connect(
                lambda: pedency.confirm()
            )

        table, stacked_widget = pedency()
        self.connections[table] = table.itemDoubleClicked.connect(
            lambda: pedency.updt()
        )
        self.connections[table] = table.itemDoubleClicked.connect(
            self.in_operation
        )
        
        stacked_widget.setParent(self.page_4)
        self.verticalLayout_3.addWidget(stacked_widget)
        return pedency
    
    def reload_pedency(self):
        """
        Recarrega as pendências e emails da empresa, caso não haja alterações pendentes.
        """
        try:
            if any([self.pedency.has_change(), self.address.has_change()]):
                raise Exception(self.message_pending_save)
                
            self.pedency.fill(*self.db.pedency(self.current_companie_id))
            self.address.fill(*self.db.emails(self.current_companie_id))
        except Exception as err:
            messagebox.showerror('Aviso', err)

    def sheet(self):
        """
        Gera e exporta o relatório de envios, conforme o contexto atual (todas empresas ou empresa selecionada).
        """
        try:
            self.disable_btns()
            date = self.__date_sheet_cast()
            if self.stackedWidget_companie.currentIndex() != 0:
                date.append(self.current_companie_id)
                
            data = self.db.history(*date)
            self._sheet = Sheet(data)

            self._sheet.upload()
            
            self.exec_load(True)
            self._thread2 = QThread()

            self._sheet.moveToThread(self._thread2)
            self._thread2.started.connect(self._sheet.write)
            self._sheet.end.connect(self._thread2.quit)
            self._sheet.end.connect(self._thread2.deleteLater)
            self._sheet.result.connect(self.open_file)
            self._thread2.finished.connect(self._sheet.deleteLater)
            self._thread2.start()
        except Exception as err:
            self.exec_load(False)
            messagebox.showerror('Aviso', err)

    def __date_sheet_cast(self):
        """
        Converte as datas dos widgets para objetos datetime.
        """
        dates = []
        for widget in self.ref_date_sheet:
            var = widget.text().split('/')
            var.reverse()
            var = map(lambda x: int(x), var)
            dates.append(datetime(*var))
        return dates

    def open_file(self, path):
        """
        Abre o arquivo gerado pelo relatório.
        """
        self.exec_load(False)
        startfile(path)

    def save(self):
        """
        Salva alterações de pendências e emails, caso existam.
        """
        try:
            self.disable_btns()
            stats_pedenc = self.pedency.has_change()
            stats_address = self.address.has_change()

            if any([stats_pedenc, stats_address]) != True:
                raise Exception(self.message_no_save)
            
            if messagebox.askyesno('Aviso', self.message_save) == False:
                return None
            
            ref_change = {}
            if stats_pedenc == True:
                ref_change[self.pedency] = self.db.changes_pedency
            
            if stats_address == True:
                ref_change[self.address] = self.db.changes_address
            
            for widget, func in ref_change.items():
                widget_change = widget.change()
                func(self.current_companie_id, widget_change)
                widget.save()
            
            # self.disable_btns()
        except EmailNotValidError:
            messagebox.showerror('Aviso', 'Defina um endereço de e-mail válido')

        except Exception as err:
            messagebox.showerror('Aviso', err)

        finally:
            self.disable_btns()

    def exit_pedency(self):
        """
        Sai da tela de pendências, descartando alterações não salvas se necessário.
        """
        """
        Sai da tela de pendências, descartando alterações não salvas se necessário.
        """
        if any([self.pedency.has_change(), self.address.has_change()]):
            if messagebox.askyesno('Aviso', self.message_exit_save) == False:
                return None

        self.pushButton_edit_func.setHidden(False)
        self.pushButton_save_func.setHidden(True)
        self.stackedWidget_companie.setCurrentIndex(0)
        self.stackedWidget_email.setCurrentIndex(0)
        self.switch_focus('companies')
        
        send_btn, page = self.address()
        page.deleteLater()
        self.stackedWidget_email.removeWidget(page)

        table, stacked_widget = self.pedency()
        stacked_widget.deleteLater()
        self.verticalLayout_3.removeWidget(stacked_widget)

    def switch_focus(self, current_widget: str):
        """
        Atualiza as conexões e tooltips dos botões conforme o contexto atual.
        """
        """
        Atualiza as conexões e tooltips dos botões conforme o contexto atual.
        """
        ref_connection = {}
        ref_tool_tip = {}

        ref_connection, ref_tool_tip = self.ref_universal[current_widget]
        self.re_connection(ref_connection)
        self.re_tool_tip(ref_tool_tip)

    def re_connection(self, ref):
        """
        Reconecta os sinais dos botões conforme o dicionário de referência.
        """
        """
        Reconecta os sinais dos botões conforme o dicionário de referência.
        """
        for widget, connection in self.connections.items():
            widget.disconnect(connection)
        self.connections.clear()

        for widget, func in ref.items():
            self.connections[widget] = widget.clicked.connect(func)

    def re_tool_tip(self, ref):
        """
        Atualiza as tooltips dos botões conforme o dicionário de referência.
        """
        """
        Atualiza as tooltips dos botões conforme o dicionário de referência.
        """
        for widget, text in ref.items():
            widget.setToolTip(text)

    def open_assign(self):
        """
        Abre a tela de assinatura de email, se não houver alterações pendentes.
        """
        """
        Abre a tela de assinatura de email, se não houver alterações pendentes.
        """
        try:
            stats_pedenc = self.pedency.has_change()
            stats_address = self.address.has_change()

            if any([stats_pedenc, stats_address]):
                raise Exception('Salve as alterações pendentes antes de prosseguir')
                
            self.groupBox_email.setTitle('Assinatura')
            self.stackedWidget_email.setCurrentIndex(1)
        
        except Exception as error:
            messagebox.showwarning(title='Aviso', message= error)

    def exit_assign(self):
        """
        Retorna à tela de email.
        """
        """
        Retorna à tela de email.
        """
        self.groupBox_email.setTitle('Email')
        self.stackedWidget_email.setCurrentIndex(2)

    def send_email(self):
        """
        Envia email com as pendências da empresa selecionada para os endereços cadastrados.
        """
        """
        Envia email com as pendências da empresa selecionada para os endereços cadastrados.
        """
        try:
            self.disable_btns()
            name_func = self.lineEdit_name_func.text()

            if name_func == '':
                raise Exception('Nome inválido')
            
            if messagebox.askyesno('Aviso', self.message_send_email) == False:
                return None

            self.exec_load(True)
            address = self.address.data()
            pedency, taxes = self.pedency.data()

            if all([address, pedency]) == False:
                raise Exception('Não há pendências ou e-mail cadastrados para essa empresa, clique em "Voltar" e adcione a informação faltante')

            self._postman = Postman(
                name_func,
                self.label_current_companie.text(),
                address, 
                pedency,
                taxes
            )
            self._thread = QThread()

            self._postman.moveToThread(self._thread)
            self._thread.started.connect(self._postman.execute)
            self._postman.end.connect(self._thread.quit)
            self._postman.end.connect(self._thread.deleteLater)
            self._postman.result.connect(self.conclusion)
            self._postman.sended.connect(self.save_history)
            self._thread.finished.connect(self._postman.deleteLater)
            self._thread.start()

        except Exception as error:
            self.disable_btns()
            self.exec_load(False)
            messagebox.showwarning(title='Aviso', message= error)

    def conclusion(self, result: str):
        """
        Exibe mensagem de conclusão do envio de email.
        """
        """
        Exibe mensagem de conclusão do envio de email.
        """
        self.local_changes.updt_sender(self.lineEdit_name_func.text())
        self.groupBox_email.setTitle('Email')
        self.stackedWidget_email.setCurrentIndex(2)
        self.exec_load(False)
        messagebox.showinfo(title='Aviso', message= result)

    def save_history(self, *args):
        """
        Salva o histórico de envio de emails no banco de dados.
        """
        """
        Salva o histórico de envio de emails no banco de dados.
        """
        name_func, companie, taxes = args

        result = []
        for i, j in list(zip(*taxes)):
            result.append(f'{i}: {j}')

        self.db.add_history(
            name_func, companie, ' | '.join(result), self.current_companie_id
        )

    def disable_btns(self):
        """
        Alterna o estado de habilitação dos botões principais.
        """
        """
        Alterna o estado de habilitação dos botões principais.
        """
        self.enable_status = not self.enable_status
        for item in self.ref_disable_btns:
            item.setEnabled(self.enable_status)

    def exec_load(self, action: bool):
        """
        Exibe ou oculta o GIF de carregamento e alterna a tela de carregamento.
        """
        """
        Exibe ou oculta o GIF de carregamento e alterna a tela de carregamento.
        """
        if action == True:
            self.movie.start()
            self.stackedWidget_body.setCurrentIndex(1)
        else:
            self.disable_btns()
            self.movie.stop()
            self.stackedWidget_body.setCurrentIndex(0)

if __name__ == '__main__':
    """
    Ponto de entrada da aplicação.
    """
    """
    Ponto de entrada da aplicação.
    """
    app = QApplication()
    window = MainWindow()
    window.show()
    app.exec()