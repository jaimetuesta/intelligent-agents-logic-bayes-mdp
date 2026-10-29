import random
import numpy as np

class RiverMDP():
    def __init__(self):
        # Todos estos valores se pueden cambiar, están escogidos para coincidir con el enunciado
        self.h = 7
        self.w = 6
        self.n_islas = 2

        self.grid = self.generate_river()
        self.riverstrength = self.generate_riverstrength()
        self.V = [[0 for i in range(self.w)] for j in range(self.h)]
        self.policy = {}
        self.gamma = 0.95  

        self.actions = ['up', 'down', 'left', 'right']

    def generate_river(self):
        grid = [['R' for i in range(self.w)] for j in range(self.h)]

        for i in range(self.h):
            grid[i][0] = ' '
            grid[i][self.w-1] = ' '

        grid[0][0] = 'C'

        exit_col = random.randint(0, self.h-1)
        grid[exit_col][self.w-1] = 'E'

        islands = []
        while len(islands) < self.n_islas:
            i = random.randint(0, self.h-1)
            j = random.randint(1, self.w-2)
            if (i,j) not in islands:
                grid[i][j] = 'I'
                islands.append((i,j))
        
        return grid
    
    def generate_riverstrength(self):
        # 0 en extremos, valor aleatorio en el resto
        strength = [0 for i in range(self.w)]
        for i in range(1, self.w-1):
            strength[i] = round(random.uniform(0.06, 0.94), 2)
        return strength
    
    def print_grid(self):
        for row in self.grid:
            for cell in row:
                print(f'| {cell} |', end='')
            print('')

        print(f"Riverstrength: {self.riverstrength}")
    
    def next_states(self, pos: tuple[int, int], a: str) -> list[tuple[int, int]]:
        # Se definen los estados posibles por acción: o bien en la dirección deseada o bien down por la corriente
        # Cualquier movimiento bloqueado por isla o borde del mapa se convierte en stay
        delta = {'up':(-1,0), 'down':(1,0), 'left':(0,-1), 'right':(0,1)}
        i, j = pos
        di, dj = delta[a]

        movement = (i+di, j+dj)
        down = (i+1, j)
        stay = (i, j)

        candidates = [] 

        # Movimiento en dirección a
        ni, nj = movement
        if 0 <= ni < self.h and 0 <= nj < self.w and self.grid[ni][nj] != 'I':
            candidates.append(movement)
        else:
            candidates.append(stay)


        # Down
        if a != 'down':
            ni, nj = down
            if 0 <= ni < self.h and 0 <= nj < self.w and self.grid[ni][nj] != 'I':
                candidates.append(down)
            else:
                if stay not in candidates:
                    candidates.append(stay)

        return candidates
    
    def p_transition(self, s: tuple[int,int], a: str, s_prime: tuple[int,int]) -> float:
        # Cada transición es la dirección elegida con probabilidad 1 - riverstrength[j] y down con probabiliad riverstrength[j]
        # Si la acción es down siempre te mueves down
        i, j = s
        strength = self.riverstrength[j]
        delta = {'up':(-1,0), 'down':(1,0), 'left':(0,-1), 'right':(0,1)}

        movement = (i + delta[a][0], j + delta[a][1])
        down = (i + 1, j)
        stay = (i, j)

        p = 0.0
        if a == 'down':
            if 0 <= down[0] < self.h and self.grid[down[0]][down[1]] != 'I':
                if s_prime == down:
                    p = 1.0
            else:
                if s_prime == stay:
                    p = 1.0
        else:
            if 0 <= movement[0] < self.h and 0 <= movement[1] < self.w and self.grid[movement[0]][movement[1]] != 'I':
                if s_prime == movement:
                    p += (1 - strength)
            else:
                if s_prime == stay:
                    p += (1 - strength)

            if 0 <= down[0] < self.h and 0 <= down[1] < self.w and self.grid[down[0]][down[1]] != 'I':
                if s_prime == down:
                    p += strength
            else:
                if s_prime == stay:
                    p += strength

        return p

        
    def reward(self, s_prime: tuple[int, int]) -> int:
        # Solo recibe argumento s' porque la recompensa solo depende de la casilla destino, no de la origen ni de la acción
        i, j = s_prime
        # Salida = 100
        if self.grid[i][j] == 'E':
            return 100
        # Isla = -100. En la práctica no llega a aplicarse: un movimiento hacia una isla deja al capitán
        # en su casilla (ver next_states y p_transition), así que las islas actúan como obstáculos
        elif self.grid[i][j] == 'I':
            return -100
        # -1 por cada paso para minimizar número de pasos
        else:
            return -1
        
    def value_iteration(self):
        V = [[0 for i in range(self.w)] for j in range(self.h)]
        policy = {}
        theta = 1e-6   # tolerancia: se para cuando ningún valor cambia más que theta
        self.iterations = 0

        # Iterar hasta que converja (siempre converge, porque gamma < 1)
        while True:
            self.iterations += 1
            delta = 0
            for i in range(self.h):
                for j in range(self.w):
                    # Las islas no tienen valor porque no se puede estar en ellas.
                    # La salida es un estado terminal: la partida acaba al llegar, así que su valor es 0
                    # (la recompensa de +100 se obtiene al entrar en ella)
                    if self.grid[i][j] in ('I', 'E'):
                        continue
                    v_old = V[i][j]
                    Q = {}

                    # Ecuación de Bellman: V_i+1(s) = max_a(sum(P(s'|s,a)[R(s') + γ*V_i(s')]))
                    for a in self.actions:
                        q = 0
                        for ni in range(self.h):
                            for nj in range(self.w):
                                p = self.p_transition((i, j), a, (ni, nj))
                                if p > 0:
                                    r = self.reward((ni, nj))
                                    q += p * (r + self.gamma*V[ni][nj])
                        Q[a] = q
                    V[i][j] = max(Q.values())
                    policy[(i, j)] = max(Q, key=Q.get) # argmax
                    delta = max(delta, abs(v_old - V[i][j])) # Cambio entre anterior iteración y esta

            # Si converge, salir del bucle
            if delta < theta:
                break

        self.V = V
        self.policy = policy
        return V, policy
    
    def simulate_policy(self, policy: dict) -> int:
        i, j = 0, 0
        total_reward = 0
        steps = 0

        while True:
            # Estado terminal
            if self.grid[i][j] == 'E':
                print(f'Salida alcanzada en {steps} pasos. Reward final: {total_reward}')
                return total_reward

            # Elegir acción y outcome
            a = policy[(i, j)]
            possibles = self.next_states((i, j), a)
            probs = [self.p_transition((i, j), a, s_prime) for s_prime in possibles]
            next_state = random.choices(possibles, weights=probs)[0]
            ni, nj = next_state

            # Indicar en terminal si el movimiento ha sido corriente o no
            by_current = (a != 'down' and ni == i + 1 and nj == j) or (ni == i and nj == j)
            if by_current:
                suffix = ' (corriente)'
            else:
                suffix = ''

            # Recompensa
            r = self.reward((ni, nj))
            total_reward += r
            print(f"Paso {steps+1}: \t({i},{j}) -{a}-> ({ni},{nj})\tr = {r}\ttotal = {total_reward}\t{suffix}")

            i, j = ni, nj

            steps += 1


def main():
    print('PROYECTO FIA PARTE 2.2 (river_mdp.py) - JAIME TUESTA DE SIMÓN')
    print('\n====================================================================================================================\n')

    river = RiverMDP()
    river.print_grid()

    print('\nVALUE ITERATION')
    V, policy = river.value_iteration()
    print(f'Convergencia en {river.iterations} iteraciones')
    print('Política óptima (π*):')
    for i in range(river.h):
        row = []
        for j in range(river.w):
            if river.grid[i][j] == 'I':
                cell = 'I'
            elif river.grid[i][j] == 'E':
                cell = 'E'
            else:
                cell = river.policy[(i, j)]
            row.append(str(cell))
        print('\t'.join(row))

    print('\n\nSIMULACIONES')
    scores = []
    for i in range(10):
        print(f'\n-- Partida {i+1} --')
        score = river.simulate_policy(policy)
        scores.append(score)
    print(f'\nPuntuación promedio: {np.mean(scores):.2f}')

if __name__ == '__main__':
    main()