function data_out = SimulinkEmisor(modo, origen, destino)
% Formatea mensajes TCP/IP para enviar al robot Ned2.
% modo:    1=INI MAN | 2=INI AUT | 3=INI COM | 4=MOV (con origen/destino) | 5=MOV (solo) | 0=MOV (con origen/destino)
% origen:  1-9 (tablero) | 11-13 (alm1-alm3)
% destino: 1-9 (tablero)
%
% data_out es siempre uint8[1×32] de tamaño fijo.

% Buffer fijo de 32 bytes relleno con LF (char 10)
data_out = uint8(10 .* ones(1, 32, 'uint8'));

msg = char(zeros(1, 0));

modo_id = round(double(modo));
if modo_id >= 1 && modo_id <= 3
    % ── Mensaje INI ──────────────────────────────────────────
    if modo_id == 1
        msg = ['INI MAN' char(10)];
    elseif modo_id == 2
        msg = ['INI AUT' char(10)];
    else
        msg = ['INI COM' char(10)];
    end
else
    % ── Mensaje MOV ──────────────────────────────────────────
    if modo_id == 5
        % Modo 5: enviar solo "MOV" sin parámetros
        msg = ['MOV' char(10)];
    else
        % Modo 0, 4 o resto: enviar "MOV origen destino"
        orig_id = round(double(origen));
        dest_id = round(double(destino));

        orig_str = char(zeros(1, 0));
        if orig_id == 11
            orig_str = 'alm1';
        elseif orig_id == 12
            orig_str = 'alm2';
        elseif orig_id == 13
            orig_str = 'alm3';
        elseif orig_id >= 1 && orig_id <= 9
            orig_str = char(real(48 + orig_id));
        end

        if ~isempty(orig_str) && dest_id >= 1 && dest_id <= 9
            msg = ['MOV ' orig_str ' ' char(real(48 + dest_id)) char(10)];
        end
    end
end

% ── Copiar msg en data_out byte a byte (tamaño siempre 32) ───
if ~isempty(msg)
    b  = uint8(msg);
    nb = min(numel(b), 31);
    for k = 1:nb
        data_out(k) = b(k);
    end
    data_out(32) = uint8(10);
end