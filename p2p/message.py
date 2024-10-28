import struct
import socket
import logging

# Cấu hình logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

class MessageID:
    MsgChoke = 0
    MsgUnchoke = 1
    MsgInterested = 2
    MsgNotInterested = 3
    MsgHave = 4
    MsgBitfield = 5
    MsgRequest = 6
    MsgPiece = 7
    MsgCancel = 8

class Message:
    def __init__(self, message_id=None, payload=None):
        self.ID = message_id
        self.Payload = payload or bytearray()

    
    @classmethod
    def format_request(cls, index, begin, length):
        payload = struct.pack('>III', index, begin, length)
        return cls(message_id=MessageID.MsgRequest, payload=payload)

    @classmethod
    def format_have(cls, index):
        payload = struct.pack('>I', index)
        return cls(message_id=MessageID.MsgHave, payload=payload)

    @classmethod
    def format_piece(cls, index, begin, block):
        payload = struct.pack('>II', index, begin) + block
        return cls(message_id=MessageID.MsgPiece, payload=payload)

    @staticmethod
    def parse_piece(index, buf, msg):
        if msg.ID != MessageID.MsgPiece:
            raise ValueError(f"Expected PIECE (ID {MessageID.MsgPiece}), got ID {msg.ID}")
        if len(msg.Payload) < 8:
            raise ValueError(f"Payload too short. {len(msg.Payload)} < 8")

        parsed_index = struct.unpack('>I', msg.Payload[0:4])[0]
        if parsed_index != index:
            raise ValueError(f"Expected index {index}, got {parsed_index}")

        begin = struct.unpack('>I', msg.Payload[4:8])[0]
        if begin >= len(buf):
            raise ValueError(f"Begin offset too high. {begin} >= {len(buf)}")

        data = msg.Payload[8:]
        if begin + len(data) > len(buf):
            raise ValueError(f"Data too long [{len(data)}] for offset {begin} with length {len(buf)}")

        buf[begin:begin + len(data)] = data
        return len(data)

    @staticmethod
    def parse_have(msg):
        if msg.ID != MessageID.MsgHave:
            raise ValueError(f"Expected HAVE (ID {MessageID.MsgHave}), got ID {msg.ID}")
        if len(msg.Payload) != 4:
            raise ValueError(f"Expected payload length 4, got length {len(msg.Payload)}")

        return struct.unpack('>I', msg.Payload)[0]

    def serialize(self):
        if self.ID is None:
            logging.debug("Sending KeepAlive message")
            return bytearray(4)  # Keep-alive message

        length = len(self.Payload) + 1  # +1 for message ID
        buf = bytearray(4 + length)
        struct.pack_into('>I', buf, 0, length)
        buf[4] = self.ID
        buf[5:] = self.Payload
        
        logging.debug(f"Sending {self.name()} with ID {self.ID} and payload length {len(self.Payload)}")
        return buf

    @staticmethod
    def read(r):
        try:
            # Kiểm tra nếu socket hợp lệ
            if r.fileno() == -1:
                logging.error("Socket is closed or invalid")
                return None, ValueError("Socket is closed or invalid")

            length_buf = r.recv(4)
            if len(length_buf) < 4:
                logging.error("Could not read length")
                return None, ValueError("Could not read length")

            length = struct.unpack('>I', length_buf)[0]
            logging.debug(f"Received message length: {length}")

            if length == 0:
                logging.debug("Received KeepAlive message")
                return None, None

            message_buf = bytearray()
            while len(message_buf) < length:
                part = r.recv(length - len(message_buf))
                if not part:
                    logging.error("Socket connection closed by peer")
                    return None, ValueError("Socket connection closed by peer")
                message_buf.extend(part)

            message_id = message_buf[0]
            payload = message_buf[1:]
            logging.debug(f"Received {Message(message_id).name()} with ID {message_id} and payload length {len(payload)}")
            return Message(message_id=message_id, payload=payload), None

        except socket.timeout:
            logging.error("Socket timed out while reading message")
            return None, TimeoutError("Socket timed out while reading message")
        except Exception as e:
            logging.error(f"Unexpected error while reading message: {e}")
            return None, e

    def name(self):
        if self.ID is None:
            return "KeepAlive"
        message_names = {
            MessageID.MsgChoke: "Choke",
            MessageID.MsgUnchoke: "Unchoke",
            MessageID.MsgInterested: "Interested",
            MessageID.MsgNotInterested: "NotInterested",
            MessageID.MsgHave: "Have",
            MessageID.MsgBitfield: "Bitfield",
            MessageID.MsgRequest: "Request",
            MessageID.MsgPiece: "Piece",
            MessageID.MsgCancel: "Cancel",
        }
        return message_names.get(self.ID, f"Unknown#{self.ID}")

    def __str__(self):
        if self.ID is None:
            return self.name()
        return f"{self.name()} [{len(self.Payload)}]"
