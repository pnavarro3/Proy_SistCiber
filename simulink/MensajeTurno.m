function mensaje = MensajeTurno(turno)
%#codegen
% Devuelve un mensaje de estado segun el valor de entrada.
% Entrada:
%   turno: 0 o 1
% Salida:
%   mensaje: uint8 1x13 (ASCII)
%            0 -> 'Espera'
%            1 -> 'Te toca jugar'

if turno == 1
    msg = 'Te toca jugar';
else
    msg = 'Espera       ';
end

mensaje = uint8(msg);

end