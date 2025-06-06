import matplotlib.pyplot as plt
import networkx as nx
import threading
import time


class GrafoVisualizador(threading.Thread):
    def __init__(self, grafo_espera: nx.DiGraph, intervalo: float = 3.0):
        super().__init__(daemon=True)  # Daemon para encerrar com o main
        self.grafo = grafo_espera
        self.intervalo = intervalo
        self._ativo = True

    def run(self):
        while self._ativo:
            self.exibir_grafo()
            time.sleep(self.intervalo)

    def parar(self):
        self._ativo = False

    def exibir_grafo(self):
        plt.clf()
        pos = nx.spring_layout(self.grafo)
        plt.title("Wait-For Graph (Grafo de Espera)")

        nx.draw(self.grafo, pos, with_labels=True, node_color='skyblue', node_size=2000, font_size=10,
                edge_color='gray', arrowsize=20)

        cycles = list(nx.simple_cycles(self.grafo))
        for ciclo in cycles:
            if len(ciclo) > 1:
                # desenhar ciclo com outra cor
                edges = list(zip(ciclo, ciclo[1:] + [ciclo[0]]))
                nx.draw_networkx_edges(self.grafo, pos, edgelist=edges, edge_color='red', width=2.5)

        plt.pause(0.1)
