function [DEC, p1, p2, p3, FTU, FIN, RES] = SimulinkReceptor(data, count)
% Parsea mensajes TCP/IP recibidos del robot Ned2.
% Entradas: data (uint8) y count (double) del bloque TCP/IP Receive.
% Mensajes: DEC | ACT p1 p2 p3 | FTU | FIN VIC|DER|EMP
%
% Reescrito sin sub-funciones para compatibilidad total con
% el generador de código de Simulink MATLAB Function.

persistent rx_buffer last_p1 last_p2 last_p3;
coder.varsize('rx_buffer', [1, 2048], [0, 1]);
if isempty(rx_buffer)
    rx_buffer = char(zeros(1, 0));
    last_p1   = 0.0;
    last_p2   = 0.0;
    last_p3   = 0.0;
end

DEC = 0.0;
FTU = 0.0;
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
        sp1 = sp_arr(1);                % escalar
        cmd = upper(linea(1 : sp1-1));
        if sp1 < numel(linea)
            resto = linea(sp1+1 : end);
        else
            resto = char(zeros(1, 0));
        end
    end

    % ── Decodificar mensaje ──────────────────────────────────
    if strcmp(cmd, 'DEC')
        DEC = 1.0;

    elseif strcmp(cmd, 'ACT')
        % Parsear "p1 p2 p3" directamente con índices fijos.
        % Formato esperado: dígitos separados por espacios, ej. "1 5 9"
        nums = [0.0, 0.0, 0.0];
        ni   = 1;                       % índice del número actual (1..3)
        val  = 0.0;
        enNum = false;
        for ci = 1:numel(resto)
            ch = resto(ci);
            if ch >= '0' && ch <= '9'
                val   = val * 10.0 + (double(ch) - 48.0);
                enNum = true;
            else
                if enNum && ni <= 3
                    nums(ni) = val;
                    ni  = ni + 1;
                    val = 0.0;
                    enNum = false;
                end
            end
        end
        if enNum && ni <= 3
            nums(ni) = val;
        end
        last_p1 = nums(1);
        last_p2 = nums(2);
        last_p3 = nums(3);

    elseif strcmp(cmd, 'FTU')
        FTU = 1.0;

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

p1 = last_p1;
p2 = last_p2;
p3 = last_p3;
