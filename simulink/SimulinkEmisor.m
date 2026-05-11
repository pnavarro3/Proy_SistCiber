function [data_out, msg_len] = SimulinkEmisor(sendmsg, modo, origen, destino)
% Formatea mensajes TCP/IP para enviar al robot Ned2.
% sendmsg: 0=nada | 1=INI(modo 1-3) | 2=MOV(origen 1-9/11-13, destino 1-9)
%
% data_out es uint8[1×32] de tamaño fijo (el coder lo ve fijo).
% msg_len  es la longitud real del mensaje (0 si no hay nada que enviar).

persistent prev_sendmsg;
if isempty(prev_sendmsg)
    prev_sendmsg = 0.0;
end

% Buffer fijo de 32 bytes relleno con LF (char 10)
data_out = uint8(10 .* ones(1, 32, 'uint8'));
msg_len  = double(0);

sm      = round(double(sendmsg));
prev_sm = round(double(prev_sendmsg));
prev_sendmsg = double(sm);

if sm > 0 && prev_sm == 0

    msg = char(zeros(1, 0));            % cadena del mensaje a construir

    switch sm

        case 1
            modo_id = round(double(modo));
            if modo_id == 1
                msg = ['INI MAN' char(10)];
            elseif modo_id == 2
                msg = ['INI AUT' char(10)];
            elseif modo_id == 3
                msg = ['INI COM' char(10)];
            end

        case 2
            orig_id = round(double(origen));
            dest_id = round(double(destino));

            orig_str = char(zeros(1, 0));
            if orig_id >= 11 && orig_id <= 13
                d = orig_id - 10;       % 1, 2 o 3
                orig_str = ['alm' char(real(48 + d))];
            elseif orig_id >= 1 && orig_id <= 9
                orig_str = char(real(48 + orig_id));
            end

            if ~isempty(orig_str) && dest_id >= 1 && dest_id <= 9
                msg = ['MOV ' orig_str ' ' char(real(48 + dest_id)) char(10)];
            end
    end

    % ── Copiar msg en data_out byte a byte (tamaño siempre 32) ──
    if ~isempty(msg)
        b  = uint8(msg);
        nb = min(numel(b), 31);         % máximo 31 bytes + LF final forzado
        for k = 1:nb
            data_out(k) = b(k);
        end
        data_out(32) = uint8(10);       % asegurar LF en última posición
        msg_len = double(nb);           % longitud real a enviar
    end
end
