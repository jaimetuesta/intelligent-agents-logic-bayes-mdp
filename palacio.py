import random
import seaborn as sns
import matplotlib.pyplot as plt

class GameState:
    def __init__(self):
        self.grid, self.positions = self.generate_grid() 
        self.grenade = True
        self.kurtz = False
        self.soldier = True
        self.scream = False
        self.exit_found = False

        # Agente bayesiano
        self.visited = []
        self.elements = ['F', 'P', 'D', 'M', 'S']
        self.beliefs = {e: self.create_prior() for e in self.elements}
        self.risk_threshold = 0.1

    def generate_grid(self):
        positions = {}

        # Cuadrícula vacía
        grid = [['□' for i in range(6)] for j in range(6)]

        # Willard
        grid[0][0] = 'W'
        positions['W'] = (0, 0)

        # Trampas
        traps = ['F', 'P', 'D']
        for t in traps:
            placed = False
            while not placed:
                row = random.randint(0, 5)
                col = random.randint(0, 5)
                if row != 0 or col != 0:
                    if grid[row][col] == '□':
                        grid[row][col] = t
                    else:
                        grid[row][col] += t
                    positions[t] = (row, col)
                    placed = True

        # Resto de elementos (militar, salida, Kurtz)
        elements = ['M', 'S', 'K']
        for e in elements:
            placed = False
            while not placed:
                row = random.randint(0, 5)
                col = random.randint(0, 5)
                occupied_by_trap = False
                for t in traps:
                    if t in grid[row][col]:
                        occupied_by_trap = True
                if not (row == 0 and col == 0) and not occupied_by_trap:
                    if grid[row][col] == '□':
                        grid[row][col] = e
                    else:
                        grid[row][col] += e
                    positions[e] = (row, col)
                    placed = True

        return grid, positions
    
    def print_grid(self) -> None:
        for i in range(6):
            for j in range(6):
                if (i, j) in self.visited or self.positions['W'] == (i, j):
                    cell = self.grid[i][j]
                elif self.exit_found and self.positions['S'] == (i, j):
                    cell = 'S'
                else:
                    cell = '■'
                print(cell, end=' ')
            print()

    def get_percepts(self) -> dict:
        row, col = self.positions['W']
        percepts = {}
        adjs = adjacents((row, col)).values()

        percepts['eF'] = False
        percepts['eP'] = False
        percepts['eD'] = False
        percepts['eM'] = False
        percepts['eS'] = False
        
        for cell in adjs:
            # Fuego
            if self.positions['F'] == cell:
                percepts['eF'] = True
            # Pinchos
            if self.positions['P'] == cell:
                percepts['eP'] = True
            # Dardos venenosos
            if self.positions['D'] == cell:
                percepts['eD'] = True
            # Militar
            if self.positions['M'] == cell:
                percepts['eM'] = True
            # Salida
            if self.positions['S'] == cell:
                percepts['eS'] = True
            
        
        # Paredes
        percepts['Pared_U'] = row == 0
        percepts['Pared_D'] = row == 5
        percepts['Pared_L'] = col == 0
        percepts['Pared_R'] = col == 5
        
        # Grito: solo si se mata al soldado
        percepts['Grito'] = self.scream
        
        # Reset grito para el siguiente turno
        self.scream = False

        return percepts
    
    def create_prior(self):
        # Prior uniforme para cada uno de los elementos: 0 en inicio, 1/35 en las casillas restantes
        prior = [[1 for i in range(6)] for j in range(6)]
        prior[0][0] = 0
        return normalize_matrix(prior)
    
    def update_beliefs(self, percepts: dict):
        # Se actualizan las visitadas ya que éstas tienen 0% de peligro
        w = self.positions['W']
        if w not in self.visited:
            self.visited.append(w)

        for element, percept in [('F','eF'), ('P','eP'), ('D','eD'), ('M','eM'), ('S','eS')]:
            observed = percepts[percept]
            adjs = list(adjacents(w).values())
            adjs.append(w)

            # Si se observa el percepto, todas las adyacentes son likelihood 1 y las no adyacentes likelihood 0
            # Si no se observa, todas las adyacentes son likelihood 0 y las no adyacentes likelihood 1
            # (Da igual el número porque luego se va a normalizar, lo importante es cuáles sí pueden ser y cuáles no)
            lik = [[0 for i in range(6)] for j in range(6)]
            for i in range(6):
                for j in range(6):
                    if (i, j) in adjs:
                        lik[i][j] = 1 if observed else 0
                    else:
                        lik[i][j] = 0 if observed else 1

            # Posterior = prior * likelihood (desnormalizado)
            unnorm = [[0 for i in range(6)] for j in range(6)]
            for i in range(6):
                for j in range(6):
                    unnorm[i][j] = lik[i][j] * self.beliefs[element][i][j]

            # Se descartan las visitadas (la salida se arregla ahora)
            for i, j in self.visited:
                unnorm[i][j] = 0

            # Se normaliza para que el heatmap sea una distribución bien definida (suma 1)
            self.beliefs[element] = normalize_matrix(unnorm)

        # Si se ha estado en la salida, la probabilidad se concentra en la casilla conocida
        if self.exit_found:
            self.beliefs['S'] = [[0 for i in range(6)] for j in range(6)]
            self.beliefs['S'][self.positions['S'][0]][self.positions['S'][1]] = 1

    def traps_belief(self):
        # Probabilidad de que haya al menos una trampa en cada casilla.
        # Las tres trampas se colocan de forma independiente y cada percepto depende solo de su trampa,
        # así que P(alguna trampa) = 1 - (1 - P(F)) * (1 - P(P)) * (1 - P(D)).
        # No se normaliza: cada casilla tiene su propia probabilidad, entre 0 y 1.
        fire = self.beliefs['F']
        spikes = self.beliefs['P']
        darts = self.beliefs['D']
        traps = [[0 for i in range(6)]for j in range(6)]
        for i in range(6):
            for j in range(6):
                traps[i][j] = 1 - (1 - fire[i][j]) * (1 - spikes[i][j]) * (1 - darts[i][j])
        return traps
    
    def plot_heatmaps(self, w: tuple[int, int]):
        # Se plotean los heatmaps con seaborn y matplotlib
        traps = self.traps_belief()
        soldier = self.beliefs['M']
        exit = self.beliefs['S']
        wi, wj = w

        fig, axs = plt.subplots(1, 3, figsize=(15,5))

        # Trampas
        im1 = sns.heatmap(traps, annot=True, fmt='.2f', cmap='Reds', cbar_kws={'label': 'P(trampa)'}, ax=axs[0], xticklabels=range(6), yticklabels=range(6))
        axs[0].set_title('Prob. alguna trampa\n(F, P o D)', fontsize=14)
        axs[0].plot(wj+.5, wi+.5, 'bo', markersize=12, markeredgecolor='black', linewidth=2)

        # Soldado
        im2 = sns.heatmap(soldier, annot=True, fmt='.2f', cmap='Reds', cbar_kws={'label': 'P(M)'}, ax=axs[1], xticklabels=range(6), yticklabels=range(6))
        axs[1].set_title('Prob. Soldado (M)', fontsize=14)
        axs[1].plot(wj+.5, wi+.5, 'bo', markersize=12, markeredgecolor='black', linewidth=2)

        # Salida
        im3 = sns.heatmap(exit, annot=True, fmt='.2f', cmap='Greens', cbar_kws={'label': 'P(S)'}, ax=axs[2], xticklabels=range(6), yticklabels=range(6))
        axs[2].set_title('Prob. Salida (S)', fontsize=14)
        axs[2].plot(wj+.5, wi+.5, 'bo', markersize=12, markeredgecolor='black', linewidth=2)

        for ax in axs:
            ax.grid(True, alpha=0.3)
            ax.set_xlabel('Columna')
            ax.set_ylabel('Fila')
        
        plt.tight_layout()
        plt.show()
        plt.close()

    def safe_moves(self, w: tuple[int, int]):
        safe_moves = []
        adjs = adjacents(w)
        for dir in adjs:
            if adjs[dir] != (-1, -1) and self.is_safe(adjs[dir]):
                safe_moves.append(dir)

        return safe_moves

    def p_danger(self, pos: tuple[int, int]) -> float:
        i, j = pos
        p_trap = self.traps_belief()[i][j]
        p_soldier = self.beliefs['M'][i][j]

        # El soldado nunca comparte casilla con una trampa: los dos sucesos son incompatibles,
        # así que la probabilidad de peligro es la suma de ambas
        return min(1.0, p_trap + p_soldier)

    def is_safe(self, pos: tuple[int, int]):
        return self.p_danger(pos) < self.risk_threshold
    

def normalize_matrix(m: list[list[float]]):
    total = 0
    for i in range(6):
        for j in range(6):
            total += m[i][j]

    if total != 0:
        for i in range(6):
            for j in range(6):
                m[i][j] /= total

    return m

    
def adjacents(coords: tuple[int, int]) -> list[tuple[int, int]]:
    row, col = coords
    adjs = {'a la derecha': (-1, -1), 'abajo': (-1, -1), 'a la izquierda': (-1, -1), 'arriba': (-1, -1)}
    if row != 0:
        adjs['arriba'] = (row-1, col)
    if row != 5:
        adjs['abajo'] = (row+1, col)
    if col != 0:
        adjs['a la izquierda'] = (row, col-1)
    if col != 5:
        adjs['a la derecha'] = (row, col+1)

    return adjs
    
def move_captain(state: GameState, dir: str) -> bool:
    dirs = {'W': (-1,0), 'S': (1,0), 'A': (0,-1), 'D': (0,1)}
    row, col = state.positions['W']
    rowf = row + dirs[dir][0]
    colf = col + dirs[dir][1]

    # Si hay pared, no dejar mover
    if rowf < 0 or colf < 0 or rowf > 5 or colf > 5: 
        print('Ahí no puedes moverte, hay una pared.')
        return True

    cell = state.grid[rowf][colf]
    state.positions['W'] = (rowf, colf)
    state.grid[rowf][colf] = 'W'

    if state.positions['S'] == (row, col):
        state.grid[row][col] = 'S'
    else:
        state.grid[row][col] = '□'

    # Trampas
    trap = False
    traps = ['F', 'P', 'D']
    for t in traps:
        if t in cell:
            trap = True
    
    if trap:
        if 'F' in cell:
            print('¡Hay una trampa de fuego! ', end='')
        if 'P' in cell:
            print('¡Hay una trampa con pinchos! ', end='')
        if 'D' in cell:
            print('¡Hay una trampa con dardos venenosos! ', end='')
        print('Mueres.')
        return False
    
    # Otros elementos
    element = False
    elements = ['M', 'K', 'S']
    for e in elements:
        if e in cell:
            element = True

    if element:
        if state.soldier and 'M' in cell:
            print('¡Está el soldado! Te mata.')
            return False
        
        if 'K' in cell:
            print('¡Encuentras a Kurtz! Lo rescatas. ', end='')
            state.kurtz = True
        
        if 'S' in cell:
            state.exit_found = True
            if 'K' in cell:
                print('¡Y estaba en la salida! Podéis salir.')
                return True
            elif state.kurtz:
                print('¡Has llegado a la salida! Puedes salir.')
                return True
            else:
                print('¡Has encontrado la salida! Pero no tienes a Kurtz. Ve a por él.')
                return True
        else:
            print('')

    return True
        
def throw_grenade(state: GameState, dir: str):
    if not state.grenade:
        print('No puedes tirar la granada, ya no la tienes.')
        return

    dirs = {'W': (-1,0), 'S': (1,0), 'A': (0,-1), 'D': (0,1)}
    row, col = state.positions['W']
    rowf = row + dirs[dir][0]
    colf = col + dirs[dir][1]

    # Si hay pared, no dejar tirar
    if rowf < 0 or colf < 0 or rowf > 5 or colf > 5: 
        print('Ahí hay una pared, no puedes tirar la granada.')
        return 
    
    state.grenade = False
    if state.positions['M'] == (rowf, colf) and state.soldier:
        state.soldier = False
        state.beliefs['M'] = [[0 for i in range(6)] for j in range(6)]
        if len(state.grid[rowf][colf]) == 1:
            state.grid[rowf][colf] = '□'
        else:
            state.grid[rowf][colf] = state.grid[rowf][colf][1:]
        state.scream = True
        print('\n¡Oyes un grito! Soldado eliminado.')
    else:
        state.beliefs['M'][rowf][colf] = 0
        print('\nNo se oye nada. El soldado sigue vivo.')

    
def exit_palace(state: GameState) -> bool:
    if state.positions['W'] == state.positions['S']:
        state.exit_found = True
        if state.kurtz:
            print('¡Sales del palacio! Enhorabuena.')
            return True
        else:
            print('No tienes a Kurtz. No puedes salir.')
            return False
    else:
        print('No estás en la salida, no puedes salir.')
        return False
    
def main():
    print('PROYECTO FIA PARTE 2.1 (palacio.py) - JAIME TUESTA DE SIMÓN')
    print('\n====================================================================================================================\n')

    state = GameState()
    # Turno
    while True: 
        # Imprimir tablero
        state.print_grid()
        print(f'Willard en {state.positions['W']}, Granada: {state.grenade}, Kurtz encontrado: {state.kurtz}, Soldado vivo: {state.soldier}')

        # Imprimir preceptos
        percepts = state.get_percepts()
        print('\nPERCEPTOS:')
        for p in percepts:
            print(f'{p} = {percepts[p]}')

        # Mostrar heatmaps
        state.update_beliefs(percepts)
        print('\nMostrando heatmaps...\n')
        state.plot_heatmaps(state.positions['W'])

        # Elegir acciones seguras
        safe = state.safe_moves(state.positions['W'])
        if len(safe) != 0:
            print(f'Movimientos seguros (p < {state.risk_threshold}): {', '.join(safe)}')
        else:
            adjs = adjacents(state.positions['W'])
            riesgos = {d: state.p_danger(c) for d, c in adjs.items() if c != (-1, -1)}
            menos_arriesgado = min(riesgos, key=riesgos.get)
            print(f'No hay movimientos seguros (p < {state.risk_threshold}). El menos arriesgado es {menos_arriesgado}, '
                  f'con probabilidad de peligro {riesgos[menos_arriesgado]:.2f}.')

        # Elegir acción
        action = input('\n¿Qué quieres hacer? (WASD para moverse, G para granada, E para salir): ').upper()
        print('')

        # Moverse
        if action in 'WASD' and action != '':
            alive = move_captain(state, action)
            if not alive:
                break

        # Granada
        elif action == 'G':
            if state.grenade:
                gdir = input('¿Dónde tiras la granada? (WASD): ').upper()
                if gdir in 'WASD':
                    throw_grenade(state, gdir)
                else:
                    print('Dirección no válida. No tiras la granada.')
            else:
                gdir = None
                throw_grenade(state, gdir)

        # Salir
        elif action == 'E':
            exit = exit_palace(state)
            if exit:
                break
        else:
            print('Acción no reconocida. Introduce una acción válida')

        print('\n====================================================================================================================\n')


if __name__ == '__main__':
    main()