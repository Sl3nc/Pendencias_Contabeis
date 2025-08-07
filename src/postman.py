from PySide6.QtCore import QObject, Signal
import pandas as pd
from content import Content
from delta_mail import DeltaMail
from assign import Assign

class Postman(QObject):
    """
    Responsável por orquestrar o envio de emails com as pendências e impostos.
    """
    sended = Signal(str, str, list)
    result = Signal(str)
    end = Signal()

    def __init__(self, name_func: str, companie: str, address: list[str], pedency: dict[list], taxes: dict[list]):
        """
        Inicializa o Postman com os dados necessários para envio.
        """
        super().__init__()
        self.name_func = name_func
        self.companie = companie
        self.address = address
        self.pedency = pedency
        self.taxes = taxes
        
        addres_join = "\n|=>".join(self.address)
        self.result_message = f'Pendências da empresa - {companie} - forem enviadas com sucesso para o(s) endereço(s):\n|=>{addres_join}'
        pass

    def execute(self):
        """
        Executa o processo de envio de email, gerando HTML, anexando assinatura e enviando.
        """
        try:
            df_pedency = pd.DataFrame(self.pedency)
            df_taxes = pd.DataFrame(self.taxes)

            assign = Assign(self.name_func)
            assign_path = assign()

            content = Content()
            html = content.html(
                df_pedency, df_taxes,
                assign_path, self.name_func
            )

            delta_mail = DeltaMail(self.companie, self.address, html)
            delta_mail.attach(assign_path)
            delta_mail.send()
            
            assign.remove_image()
            
            self.sended.emit(
                self.name_func, self.companie, list(self.taxes.values())
            )
            self.result.emit(self.result_message)
            self.end.emit()
        except Exception as error:
            self.result.emit(error)