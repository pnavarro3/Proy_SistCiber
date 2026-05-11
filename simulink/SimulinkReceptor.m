function [DEC, FTU, FTJ, FIN, RES, tablero] = SimulinkReceptor(data, count, Ts)
% Parsea mensajes TCP/IP recibidos del robot Ned2.
% Entradas: data (uint8), count (double) del bloque TCP/IP Receive,
%           Ts (double) periodo de muestreo del bloque (s).
% 
% Mensajes soportados:
%   - DEC: decisión de la IA tomada
%   - ACT _X_OX_O__: estado completo del tablero (9 caracteres)
%   - FTU: fin de turno del usuario/rival
%   - FTJ: fin de turno del robot
%   - FIN VIC/DER/EMP: fin de partida (victoria/derrota/empate)
%
% Salidas:
%   DEC, FTU, FTJ, FIN: pulsos (1 durante 100ms)
%   RES: resultado final (1=victoria, 2=derrota, 3=empate)
%   tablero: vector 1x9 double (0=vacío, 1=rival, 2=propio)

persistent rx_buffer dec_cnt ftu_cnt ftj_cnt tablero_mem initialized;
coder.varsize('rx_buffer', [1, 2048], [0, 1]);

if isempty(initialized)
    initialized   = true;
    rx_buffer     = char(zeros(1, 0));
    dec_cnt       = 0.0;
    ftu_cnt       = 0.0;
    ftj_cnt       = 0.0;
    tablero_mem   = zeros(1, 9);  % 0=vacío, 1=rival, 2=propio
end

PULSE_SAMPLES = max(1.0, round(0.1 / Ts));   % 100 ms en muestras

% Inicializar salidas
DEC = 0.0;
FTU = 0.0;
FTJ = 0.0;
FIN = 0.0;
RES = 0.0;

% ── Acumular bytes recibidos ──────────────────────────────────
n = round(double(count));
if n > 0
    lim    = min(n, numel(data));
    nuevos = char(data(1:lim)');
    nuevos(nuevos == char(0)) = [];
    rx_buffer = [rx_buffer, nuevos];
end

% ── Procesar líneas completas (bucle acotado) ─────────────────
for iter = 1:256                        %#ok<FORPF>
    nl_arr = find(rx_buffer == char(10) | rx_buffer == char(13), 1);
    if isempty(nl_arr)
        break;
    end
    idx = nl_arr(1);                    % forzar escalar

    % Extraer línea
    if idx > 1
        linea = strtrim(rx_buffer(1 : idx-1));
    else
        linea = char(zeros(1, 0));
    end

    % Consumir buffer
    if idx < numel(rx_buffer)
        rx_buffer = rx_buffer(idx+1 : end);
    else
        rx_buffer = char(zeros(1, 0));
    end

    if isempty(linea)
        continue;
    end

    % ── Extraer comando (primera palabra) ────────────────────
    sp_arr = find(linea == ' ', 1);
    if isempty(sp_arr)
        cmd   = upper(linea);
        resto = char(zeros(1, 0));
    else
        sp1 = sp_arr(1);
        cmd = upper(linea(1 : sp1-1));
        if sp1 < numel(linea)
            resto = linea(sp1+1 : end);
        else
            resto = char(zeros(1, 0));
        end
    end

    % ── Decodificar mensaje ──────────────────────────────────
    % Procesar ACT (mensaje con estado completo del tablero)
    if strcmp(cmd, 'ACT')
        % Formato: ACT _X_OX_O__ (9 caracteres, row-major)
        % '_' = vacío, 'X' = rival, 'O' = propio
        tablero_str = strtrim(resto);
        if length(tablero_str) >= 9
            for k = 1:9
                ch = tablero_str(k);
                if ch == 'X'
                    tablero_mem(k) = 2.0;  % rival
                elseif ch == 'O'
                    tablero_mem(k) = 1.0;  % propio
                else
                    tablero_mem(k) = 0.0;  % vacío
                end
            end
        end

    elseif strcmp(cmd, 'DEC')
        dec_cnt = PULSE_SAMPLES;

    elseif strcmp(cmd, 'FTU')
        ftu_cnt = PULSE_SAMPLES;

    elseif strcmp(cmd, 'FTJ')
        ftj_cnt = PULSE_SAMPLES;

    elseif strcmp(cmd, 'FIN')
        FIN = 1.0;
        r   = strtrim(resto);
        if numel(r) >= 1
            c1 = upper(r(1));
            if     c1 == 'V',  RES = 1.0;
            elseif c1 == 'D',  RES = 2.0;
            elseif c1 == 'E',  RES = 3.0;
            end
        end
    end
end

% ── Actualizar contadores de pulso (mantener salida a 1 durante 100 ms)
if dec_cnt > 0
    DEC = 1.0;
    dec_cnt = dec_cnt - 1.0;
end

if ftu_cnt > 0
    FTU = 1.0;
    ftu_cnt = ftu_cnt - 1.0;
end

if ftj_cnt > 0
    FTJ = 1.0;
    ftj_cnt = ftj_cnt - 1.0;
end

% ── Asignar salidas
tablero = tablero_mem;
end