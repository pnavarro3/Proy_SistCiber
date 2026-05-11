function [c1, c2, c3, c4, c5, c6, c7, c8, c9] = InterpretarTablero(tablero)
%#codegen
% Extrae 9 variables escalares del vector 1x9 del tablero.
%
% Entrada:
%   tablero: vector double 1x9 (0=vacío, 1=rival, 2=propio)
%
% Salidas:
%   c1-c9: valor de cada casilla
%
% Mapeo:  1 2 3
%         4 5 6
%         7 8 9

c1 = tablero(1); c2 = tablero(2); c3 = tablero(3);
c4 = tablero(4); c5 = tablero(5); c6 = tablero(6);
c7 = tablero(7); c8 = tablero(8); c9 = tablero(9);

end
