import random

class GameState:
    def __init__(self):
        self.grid, self.positions = self.generate_grid() 
        self.grenade = True
        self.kurtz = False
        self.soldier = True
        self.scream = False
        self.exit_found = False

        # KB
        self.visited = []
        self.history = []

        self.possible_P = [(i,j) for i in range(6) for j in range(6)]
        self.possible_S = [(i,j) for i in range(6) for j in range(6)]
        self.possible_E = [(i,j) for i in range(6) for j in range(6)]
        self.confirmed_P = []

    
    def generate_grid(self) -> list[list[str]]:
        positions = {}

        # Cuadrícula vacía
        grid = [['□' for i in range(6)] for j in range(6)]

        # Willard
        grid[0][0] = 'W'
        positions['W'] = (0, 0)

        # Precipicios
        i = 0
        positions['P'] = []
        while i < 3:
            row = random.randint(0,5)
            col = random.randint(0,5)
            if grid[row][col] == '□':
                grid[row][col] = 'P'
                positions['P'].append((row, col))
                i += 1

        # Soldado
        soldier = False
        while not soldier:
            row = random.randint(0,5)
            col = random.randint(0,5)
            if grid[row][col] == '□':
                grid[row][col] = 'S'
                positions['S'] = (row, col)
                soldier = True

        # Posición de Kurtz
        coronel = False
        while not coronel:
            row = random.randint(0,5)
            col = random.randint(0,5)
            if grid[row][col] == '□':
                grid[row][col] = 'K'
                positions['K'] = (row, col)
                coronel = True

        # Salida
        exit = False
        while not exit:
            row = random.randint(0,5)
            col = random.randint(0,5)
            if grid[row][col] == '□':
                grid[row][col] = 'E'
                positions['E'] = (row, col)
                exit = True

        return grid, positions

    def print_grid(self) -> None:
        for i in range(6):
            for j in range(6):
                if (i, j) in self.visited or self.positions['W'] == (i, j):
                    cell = self.grid[i][j]
                elif self.exit_found and self.positions['E'] == (i, j):
                    cell = 'E'
                elif len(self.confirmed_P) == 3 and (i, j) in self.positions['P']:
                    cell = 'P'
                elif self.soldier and len(self.possible_S) == 1 and self.positions['S'] == (i, j):
                    cell = 'S'
                else:
                    cell = '■'
                print(cell, end=' ')
            print()

    def get_percepts(self) -> dict:
        row, col = self.positions['W']
        percepts = {}
        adjs = adjacents((row, col)).values()


        percepts['Brisa'] = False
        percepts['Ronquido'] = False
        if self.positions['E'] == (row, col):
            percepts['Resplandor'] = True
        else:
            percepts['Resplandor'] = False

        for cell in adjs:
            # Brisa (detector de P)
            if cell in self.positions['P']:
                percepts['Brisa'] = True
            # Ronquido (detector de S)
            if self.soldier and self.positions['S'] == cell:
                percepts['Ronquido'] = True
            # Resplandor (detector de E)
            if self.positions['E'] == cell:
                percepts['Resplandor'] = True
        
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
    
    def update_kb(self):
        pits = self.possible_P
        soldier = self.possible_S
        exit = self.possible_E

        for pos, percepts in self.history:
            adjs = adjacents(pos)

            breeze = percepts['Brisa']
            snore = percepts['Ronquido']
            shine = percepts['Resplandor']

            # Si no se recibe la señal, se descartan todos los adyacentes
            # (En pits no funciona porque hay 3) Si se recibe la señal, se descartan todos los no adyacentes
            if not breeze:
                pits = [s for s in pits if s not in adjs.values()]
                    
            if self.soldier:
                if snore:
                    soldier = [cell for cell in soldier if cell in adjs.values()]
                else:
                    soldier = [cell for cell in soldier if cell not in adjs.values()]    

            if shine:
                exit = [cell for cell in exit if cell in adjs.values()]
            else:
                exit = [cell for cell in exit if cell not in adjs.values()]

        # Se descartan también todas las visitadas
        pits = [s for s in pits if s not in self.visited]
        soldier = [s for s in soldier if s not in self.visited]
        # Mientras no se haya encontrado la salida, ninguna casilla visitada puede ser la salida
        exit = [s for s in exit if s not in self.visited]

        self.possible_P = pits
        self.possible_S = soldier
        # La salida puede estar visitada, no funciona lo hecho con pits y soldier
        if not self.exit_found:
            self.possible_E = exit
        else:
            self.possible_E = [self.positions['E']]

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

    if state.positions['E'] == (row, col):
        state.grid[row][col] = 'E'
    else:
        state.grid[row][col] = '□'

    # Caso precipicio
    if cell == 'P':
        print('¡Hay un precipicio! Caes y mueres.')
        return False
    
    # Caso soldado
    elif cell == 'S' and state.soldier:
        print('¡Está el soldado! Te mata.')
        return False
    
    # Caso Kurtz
    elif cell == 'K':
        print('¡Encuentras a Kurtz! Lo rescatas.')
        state.kurtz = True
        return True
    
    elif cell == 'E':
        state.exit_found = True
        if state.kurtz:
            print('¡Has llegado a la salida! Puedes salir.')
            return True
        else:
            print('¡Has encontrado la salida! Pero no tienes a Kurtz. Ve a por él.')
            return True
        
    else:
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
    if state.positions['S'] == (rowf, colf) and state.soldier:
        state.soldier = False
        state.grid[rowf][colf] = '□'
        state.scream = True
        print('\n¡Oyes un grito! Soldado eliminado.')
    else:
        print('\nNo se oye nada. El soldado sigue vivo.')
        if (rowf, colf) in state.possible_S:
            state.possible_S.remove((rowf, colf))

def exit_palace(state: GameState) -> bool:
    if state.positions['W'] == state.positions['E']:
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

    print('PROYECTO FIA PARTE 1 (kurtz.py) - JAIME TUESTA DE SIMÓN')
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

        # Actualizar KB
        if state.positions['W'] not in state.visited:
            state.visited.append(state.positions['W'])
        state.history.append((state.positions['W'], percepts))
        state.update_kb()

        # Imprimir información inferida
        print('\nSOLDADO: ', end='')
        if state.soldier:
            soldiers = state.possible_S
            adjs = adjacents(state.positions['W'])
            # Si no se ha inferido nada aún: no se da información
            if len(soldiers) > 3:
                print('No hay información suficiente. Sigue explorando.')
            # Si se sabe donde está: se da la ubicación (con dirección si adyacente)
            elif len(soldiers) == 1:
                soldier = soldiers[0]
                prefix = 'en'
                for dir in adjs:
                    if soldier == adjs[dir]:
                        prefix = dir
                print(f'¡Encontrado! Está {prefix} {state.possible_S[0]}')
            # Si pueden ser varios: se da la lista
            else:
                str_s = ''
                for s in soldiers:
                    prefix = 'en'
                    for dir in adjs:
                        if s == adjs[dir]:
                            prefix = dir
                    str_s += f'{prefix} {str(s)}, '
                print(f'Posibles ubicaciones: {str_s[:-2]}')
        else:
            # Si el soldado está muerto, no hay nada que inferir
            print(f'Muerto. Estaba en {state.positions['S']}')

        print('\nSALIDA: ', end='')
        exits = state.possible_E
        adjs = adjacents(state.positions['W'])
        # Si no se ha inferido nada aún: no se da información
        if len(exits) > 3:
            print('No hay información suficiente. Sigue explorando.')
        # Si se sabe donde está: se da la ubicación (con dirección si adyacente)
        elif len(exits) == 1:
            exit = exits[0]
            prefix = 'en'
            for dir in adjs:
                if exit == adjs[dir]:
                    prefix = dir
            print(f'¡Encontrada! Está {prefix} {state.possible_E[0]}')
        # Si pueden ser varios: se da la lista
        else:
            str_e = ''
            for e in exits:
                prefix = 'en'
                for dir in adjs:
                    if e == adjs[dir]:
                        prefix = dir
                str_e += f'{prefix} {str(e)}, '
            print(f'Posibles ubicaciones: {str_e[:-2]}')

        # Para precipicios: se dan posibilidades de precipicio en casillas adyacentes
        print('\nPRECIPICIOS: ', end='')
        adj_p = ''
        adjs = adjacents(state.positions['W'])
        for dir in adjs:
            if adjs[dir] in state.possible_P:
                adj_p += f'{dir} {str(adjs[dir])}, '
        if adj_p:
            print(f'Podría haber precipicios: {adj_p[:-2]}')

        adj_possible_pits = [p for p in adjs.values() if p in state.possible_P]

        # Si se recibe la señal de brisa y solo hay un posible precipicio, se marca como confirmado
        if len(adj_possible_pits) == 1 and adj_possible_pits[0] not in state.confirmed_P:
            state.confirmed_P.append(adj_possible_pits[0])

        adj_confirmed_pits = [p for p in adjs.values() if p in state.confirmed_P]

        # En todos los turnos se muestran los precipicios confirmados
        if len(state.confirmed_P) != 0:
            str_p = ''
            for p in state.confirmed_P:
                prefix = 'en'
                for dir in adjs:
                    if p == adjs[dir]:
                        prefix = dir
                str_p += f'{prefix} {str(p)}, '
            print(f'Precipicios encontrados: {str_p[:-2]}')

        if len(adj_possible_pits) == 0 and len(adj_confirmed_pits) == 0:
            print('En las casillas adyacentes no hay precipicios.')       

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
