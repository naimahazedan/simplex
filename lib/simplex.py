from lib.tableau import Tableau

class Simplex(object):
    """Object that represents a linear programming problem that can be
    solved by the simplex algorithm."""
    def __init__(self, F, A, B):
        """F is the objective funcion, A is the restriction functions
        and B is the value of the restriction functions"""

        assert len(F) == len(A[0])
        assert len(A) == len(B)

        self.tab = Tableau(F, A, B) # main tableau
        self.total_iter = 0  # total number of iterations
        self.iter1 = 0 # phase 1 iterations
        self.iter2 = 0 # phase 2 iterations
        self.hist = [] # historico de (tableaus, solutions)
        self.v    = 0  # best value for F til now
        self.update() # set variables values and states
        self.ans = 3  # type of problem
        self.y = []


    def __str__(self):
        """Print the iterations of the simplex steps."""
        s = self.tab.__str__()
        s += "\n"
        if self.ans == 0:
            s += ("Optimal solution:\n")
            s += ("Iterations: %d + %d = %d\n" % (self.iter1,\
                    self.iter2, self.iter))
            s += ("v = %.2f" % self.v)
            for i in range(len(self.tab.vars)):
                s += (", x%d = %.2f" % \
                        (i, self.tab.vars[i]))
            s += ("\n")
        elif self.ans == 1:
            s += ("Multiple solutions:\n")
            s += ("Iterations: %d + %d = %d\n" % (self.iter1,\
                    self.iter2, self.iter))
            s += ("v = %.2f" % self.v)
            for i in range(len(self.tab.vars)):
                s += (", x%d = %.2f" % \
                        (i, self.tab.vars[i]))
            s += ("\n")
        elif self.ans == 2:
            s += ("Unbounded solutions:\n")
            s += ("Iterations: %d + %d = %d\n" % (self.iter1,\
                    self.iter2, self.iter))
            s += ("Value and variables tend to infinity.\n")
        elif self.ans == 3:
            s += ("Impossible to solve.\n")

        return s


    def update(self):
        """Set value and state (basis or not) of the vars."""
        self.tab.set_vars()
        self.v = -1*self.tab.m[0][-1]
        self.total_iter = self.iter1 + self.iter2


    def solve(self, verbose = False):
        """Solve the simplex problem with the tableau
        simplex algorithm."""
        state = 0
        if not self.is_possible():
            if verbose:
                print("Initializing phase 1.\n")
            state = self.phase1(verbose)
            if verbose:
                print("...phase 1 done.\n")
        else:
            if verbose:
                print("All non-basic variables in 0 is possible",)
                print("solution.\n")
                print("...skipping phase 1.\n")

        self.ans = state

        if state == 0:
            if verbose:
                print("Initializing phase 2.")
            state, aux = self.phase2(verbose)
            if verbose:
                print("...phase 2 done.\n")
            self.update()
            if state == 0:
                if verbose:
                    print("Optimal solution:")
                    print("Iterations: %d (phase 1) + %d (phase 2) = %d" \
                            % (self.iter1, self.iter2,\
                            self.total_iter))
                    print("v = %.2f" % self.v, end="")
                    for i in range(len(self.tab.vars)):
                        print(", x%d = %.2f" % \
                                (i, self.tab.vars[i]), end="")
                    print("\n")
                print("Done.")
                return 0
            elif state == 1:
                if verbose:
                    print("Multiple solutions")
                    print("Showing one optimal solution:")
                    print("Iterations: %d (phase 1) + %d (phase 2) = %d" \
                            % (self.iter1, self.iter2,\
                            self.total_iter))
                    print("v = %.2f" % self.v, end="")
                    for i in range(len(self.tab.vars)):
                        print(", x%d = %.2f" % \
                                (i, self.tab.vars[i]), end="")
                    print("\n")
                print("Done.")
                return 1
            elif state == 2:
                if verbose:
                    print("Unbounded solution")
                    print("Iterations: %d (phase 1) + %d (phase 2) = %d" \
                            % (self.iter1, self.iter2,\
                            self.total_iter))
                    print("v and solutions tend to infinity.")
                print("Done.")
                return 2
            else:
                print("Impossible to solve.")
                return 3
        print("Impossible to find initial values for variables.")
        return 4


    def phase1(self, verbose = False):
        """First phase of the simplex algorithm."""
        state = 0
        M = self.tab.m
        F = [0]*(self.tab.columns-1)
        A = self.tab.const_func
        B = self.tab.const_vals

        # Add columns to the constraints and to the obj function
        for e in self.tab.y:
            F.append(1)
            for i in range(1,self.tab.lines):
                if (i) == e[0]:
                    A[i-1].append(1)
                else:
                    A[i-1].append(0)

        # Add y to the basis
        for j in range(len(F)):
            if F[j] == 1:
                for l in A:
                    if l[j] == 1:
                        F = [F[i] - l[i] for i in range(len(F))]

        # Create new tableau
        phase_one = Simplex(F, A, B)

        if verbose:
            print("Iteration 0")
            print(phase_one.tab)
            print("\n")


        # Solve
        while(not phase_one.is_best() and state == 0):
            phase_one.hist.append((phase_one.tab.m, phase_one.tab.vars))
            state, aux = phase_one.iterate(verbose)
            self.iter1 += 1
            phase_one.update()

            if verbose:
                print("Iteration %d" % self.iter1)
                print(phase_one.tab)
                print("\n")

        if (state != 0):
            state =  4

        else:
            for i in range(1,self.tab.lines):
                for j in range(self.tab.columns-1):
                    self.tab.m[i][j] = phase_one.tab.m[i][j]
                self.tab.m[i][-1] = phase_one.tab.m[i][-1]

        M = [e for e in self.tab.obj_func] + [0]

        for l in range(1,len(self.tab.m)):
                self.tab.m[0] = self.tab.sum_to_line(0,\
                        self.tab.mult_line_by(l,\
                        -1*self.tab.m[0][phase_one.tab.basis[l-1]]))

        self.update()

        return state


    def phase2(self, verbose):
        """Second phase of the simplex algorithm."""
        aux = None
        i = 0
        state = 0
        if verbose:
            print("Iteration %d" % i)
            print(self.tab)
            print("v = %.2f" % self.v,end="")
            for j in range(len(self.tab.vars)):
                print(", x%d = %.2f" % (j+1, self.tab.vars[j]),end="")
            print("\n")
        while(not self.is_best() and state == 0):
            i += 1
            self.hist.append((self.tab.m, self.tab.vars))
            state, aux = self.iterate(verbose)
            self.iter2 += 1
            self.update()

            if [e != 0 for e in self.tab.m[0][:-1]].count(True) <\
                    (self.tab.columns - len(self.tab.basis) -1):
                        state = 1

            if verbose:
                print("Iteration %d" % i)
                print(self.tab)
                print("v = %.2f" % self.v, end="")
                for j in range(len(self.tab.vars)):
                    print(", x%d = %.2f" % (j, self.tab.vars[j]),\
                            end="")
                print("\n")

        self.iter2 = i

        return state, aux


    def iterate(self, verbose):
        """Iteration of the simplex algorithm. One variable leaves
        the basis and another enter in its place."""
        M = self.tab.m
        aux = None


        if [e != 0 for e in M[0][:-1]].count(True) == 1:
            return 1, leave

        # min coefficient enters basis

        min_coef = 0 # minimum coefficient in the objective func
        enter = None # index in the list self.sol of the variable
                     # with minimum coefficient

        for i in range(len(M[0][:-1])):
            if (M[0][i] < min_coef):
                enter = i
                min_coef = M[0][i]

        if verbose:
            print("Enter: x%d" % enter)

        # min value leaves basis

        min_val = None  # minimum value in RHS/(enter colum)
        drop = None  # index in the list self.sol of the variable
                     # with minimum positive value

        for i in range(1, len(M)):
            if (M[i][enter] > 0) and\
                    ((drop == None) or (M[i][-1]/float(M[i][enter])\
                    < min_val)):
                drop = i
                min_val = M[i][-1]/float(M[i][enter])

        if drop == None:
            return 2, aux

        leave = self.tab.basis[drop-1]
        # self.tab.basis[drop-1] = enter

        if verbose:
            print("Leave: x%d" % leave)
            print("\n")

        # tableau

        M[drop] = self.tab.mult_line_by(drop, 1/float(M[drop][enter]))

        for i in range(len(M)):
            if i != drop:
                M[i] = self.tab.sum_to_line(i, self.tab.mult_line_by(\
                        drop, -1*M[i][enter]))

        self.tab.m = M

        return 0, aux


    def is_possible(self):
        """Return True if it has solution, return False otherwise."""
        for l in self.tab.m:
            val = 0
            for i in range(len(l[:-1])):
                val += (self.tab.vars[i])*l[i]
            if val != l[-1]:
                return False
        return True


    def is_best(self):
        """Return True if is optimal solution,
        otherwise return False"""
        return not any([e < 0 for e in self.tab.m[0][:-1]])

