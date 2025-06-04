from threading import Thread, Lock
from networkx import DiGraph, simple_cycles
from typing import Dict
from src.exceptions.abort_exeception import AbortException
from src.models.recurso import Recurso
from src.models.transacao_info import TransacaoInfo
from src.utils.logging import log_info, log_critical, log_error, log_success, log_warning, log_lock_unlock
from src.utils.control_time import delay

class Transacao(Thread):
    def __init__(
        self,
        info: TransacaoInfo,
        recursos: Dict[str, Recurso],
        grafo_espera: DiGraph,
        lock_global: Lock,
        transacoes_timestamp: Dict[str, TransacaoInfo],
    ):
        super().__init__()
        self.tid: str = info.tid
        self.timestamp: int = info.timestamp
        self.recursos: Dict[str, Recurso] = recursos
        self.grafo_espera: DiGraph = grafo_espera
        self.lock_global: Lock = lock_global
        self.terminada: bool = False
        self.transacoes_timestamp = transacoes_timestamp

    def run(self) -> None:
        """
        Faz o lock e unlock dos recursos
        """

        while not self.terminada:
            log_info(f"[INÍCIO] T({self.tid}) entrou em execução.")

            try:
                if self.timestamp % 2 == 0:
                    delay()
                    self.lock_recurso('X')

                    delay()
                    self.lock_recurso('Y')

                    delay()
                    self.unlock_recurso('X')

                    delay()
                    self.unlock_recurso('Y')

                else:
                    delay()
                    self.lock_recurso('Y')

                    delay()
                    self.lock_recurso('X')

                    delay()
                    self.unlock_recurso('Y')

                    delay()
                    self.unlock_recurso('X')

                delay()
                log_success(f"[COMMIT] T({self.tid}) finalizou sua execução.")  

            except AbortException:
                log_error(f"[FINALIZAÇÃO] T({self.tid}) abortada com sucesso.")
                # reinicia a transação após ser abortada

            finally:
                self.terminada = True

    def lock_recurso(self, item: str) -> bool:
        """
        Bloqueia o recurso, para que outros processos não possam
        utilizar ele

        Args:
            item (str): Nome do recurso a ser bloqueado

        Returns:
            bool: Retorna verdadeiro se o recurso foi bloqueado pelo processo
            corretamente
        """

        recurso = self.recursos[item]

        # Caso 1: recurso livre e nenhum processo em espera do recurso → trava imediatamente
        if recurso.valor_lock is None and not recurso.fila_espera:
            with self.lock_global:
                recurso.valor_lock = True
                recurso.transacao = self.tid
                log_lock_unlock(f"[LOCK] T({self.tid}) obteve lock em {item}")
                return True

        # Caso 2: a transação já possui o lock → nada a fazer
        elif recurso.transacao == self.tid:
            return True

        # Caso 3: recurso ocupado por outra transação → entra em espera
        else:
            other_tid = recurso.transacao

            # Entra na fila de espera do recurso
            recurso.fila_espera.append(self.tid)
            log_info(f"[ESPERA] T({self.tid}) esperando por {item} que está com T({other_tid})")

            # Adiciona aresta no grafo de espera (self depende de other)
            if other_tid is not None:
                self.grafo_espera.add_edge(self.tid, other_tid) 

            # Loop de espera ativo até conseguir o lock ou ser abortada
            contador_espera = 0
            while (recurso.transacao != self.tid) and not self.terminada:
                delay(0.5) # verificar a cada 50 milessimos

                contador_espera += 1
                if contador_espera % 10 == 0:
                    log_warning(f"[DEBUG] T({self.tid}) ainda esperando por {item} depois de {contador_espera * 0.5:.1f}s")
                    
                    cycles = list(simple_cycles(self.grafo_espera))
                    print("Ciclos no grafo de espera:", cycles)
                    
                    is_there_deadlock = any(self.tid in cycle for cycle in cycles)
                    print("Deadlock envolvendo T({}): {}".format(self.tid, is_there_deadlock))
                    
                    print("ID do recurso:", recurso.item_id)
                    print("Valor do lock do recurso:", recurso.valor_lock)
                    print("Fila de espera do recurso:", recurso.fila_espera)

                with self.lock_global:
                    # Se recurso estiver livre e for o primeiro da fila → pega o lock
                    # Somente pega quem for o primeiro da fila
                    if recurso.valor_lock is None and (not recurso.fila_espera or recurso.fila_espera[0] == self.tid):
                        recurso.valor_lock = True
                        recurso.transacao = self.tid

                        # Remove ele da filou do recurso, pois acabou de pegar o recurso
                        if self.tid in recurso.fila_espera:
                            recurso.fila_espera.remove(self.tid)

                        # Remove do grafo de espera, pois pegou o recurso
                        if self.grafo_espera.has_edge(self.tid, other_tid):
                            self.grafo_espera.remove_edge(self.tid, other_tid)

                        log_lock_unlock(f"[LOCK] T({self.tid}) obteve lock em {item}")

                        return True

                # Se foi detectado deadlock, aplicar wait-die
                if self.detect_deadlock():
                    log_warning(f"""[DEADLOCK] Detectado envolvendo T({self.tid}) e T({recurso.transacao}). 
                                Ambas desejam R({recurso.item_id}))""")
                    
                    # Se o recurso ainda estiver com uma transação ocupando ele, mate a transação
                    if recurso.transacao is not None:
                        self.apply_wait_die(recurso)
                        return False
                    
                    # Se o recurso não estiver mais ocupado, tente obter ele novamente
                    else:
                        continue
        
        return False
                        

    def unlock_recurso(self, item: str) -> None:
        """
        Desbloqueia o recurso, para que outros processos
        possam utilizar ele

        Args:
            item (str): Nome do recurso a ser desbloqueado
        """

        recurso = self.recursos[item]
        with self.lock_global:

            # Se a transação atual está ocupando o recurso
            if recurso.transacao == self.tid:
                
                # Libera o recurso
                recurso.valor_lock = None
                recurso.transacao = None
                log_info(f"[UNLOCK] T({self.tid}) liberou {item}")

    def detect_deadlock(self) -> bool:
        """
            Detecta a ocorrência de deadlock, onde duas ou mais threads estão bloqueadas, cada uma
            esperando por um recurso que a outra detém, impossibilitando que qualquer uma avance

        Returns:
            bool: True if exists an deadlock, else False
        """

        try:
            # Get list of deadlocks (cycles) in the system
            cycles = list(simple_cycles(self.grafo_espera))

            # Check if this transaction is in any of those deadlocks
            is_there_deadlock = any(self.tid in cycle for cycle in cycles)
            return is_there_deadlock
        except Exception:
            return False
    
    def apply_wait_die(self, recurso: Recurso) -> bool:
        """
        Se a transação atual for mais velha que a transação com que ela está competindo no deadlock,
        ela continua esperando o recurso ser liberado. Caso seja mais nova, ela se mata

        Args:
            recurso (Recurso): O recurso que está envolvido com o deadlock

        Returns:
            bool: Retorna verdadeiro se precisar aplicar o wait and die e abortar
        """

        if recurso.transacao is None:
            return False

        minha_ts = self.timestamp
        outra_ts = self.transacoes_timestamp[recurso.transacao].timestamp

        if minha_ts < outra_ts:
            log_critical(f"[WAIT-DIE] T({self.tid}) é mais velha que T({recurso.transacao}) → continua esperando")
            return False
        else:
            log_critical(f"[WAIT-DIE] T({self.tid}) é mais nova que T({recurso.transacao}) → será abortada")
            self.abort(recurso)

            return True
    
    def abort(self, recurso: Recurso) -> bool:
        """
        Mata a transação que chamou a função

        Args:
            recurso (Recurso): Recurso em que o deadlock ocorre

        Raises:
            AbortException: Indica ao programa que a transação precisa ser abortada

        Returns:
            bool: Retorna verdadeiro se a transação for abortada com sucesso
        """

        transacao_para_matar: str = self.tid

        try:
            # Remove a transação de todas as filas dos recursos
            for recurso in self.recursos.values():
                if transacao_para_matar in recurso.fila_espera:
                    recurso.fila_espera.remove(transacao_para_matar)

                if recurso.transacao == transacao_para_matar: # talvez muudar para chamar o unlock
                    # Release held lock
                    recurso.valor_lock = None
                    recurso.transacao = None
                    log_lock_unlock(f"[FORCE UNLOCK] T({transacao_para_matar}) liberou {recurso.item_id}")
                    print(recurso.fila_espera)

            # 2. Remove transação para matar do grafo
            if self.grafo_espera.has_node(transacao_para_matar):
                self.grafo_espera.remove_node(transacao_para_matar)

            # 3. Marca que a transação abortada está finalizada
            self.terminada = True

            raise AbortException()
        
        except AbortException:
            for recurso in self.recursos.values():
                if recurso.fila_espera:
                    # Forçar primeiro da fila a reavaliar lock
                    next_tid = recurso.fila_espera[0]
                    print(f"[DEBUG] Após abort de {transacao_para_matar}, próxima da fila de {recurso.item_id} é {next_tid}")

            log_error(f"[ABORT] T({transacao_para_matar}) foi abortada durante tentativa de lock")
            raise
        
        except Exception as e:
            print(f"Exceção ao tentar matar transação: {e.with_traceback}")
            return False