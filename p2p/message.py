import struct
import socket
import logging
import bencodepy
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
    MsgExtended = 20
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
    
    @classmethod
    def format_extended(cls, ext_id, payload):
        payload = struct.pack('>B', ext_id) + payload
        return cls(message_id=MessageID.MsgExtended, payload=payload)
    
    @classmethod
    def format_metadata_request(cls, piece_index):
        # `msg_type` 0 is used for metadata requests
        payload = struct.pack('>B', 0) + bencodepy({'msg_type': 0, 'piece': piece_index})
        return cls.format_extended(ext_id=20, payload=payload)

    @classmethod
    def format_metadata_data(cls, piece_index, data):
        # `msg_type` 1 is used for metadata data (response)
        payload = struct.pack('>B', 1) + bencodepy({'msg_type': 1, 'piece': piece_index, 'total_size': len(data)}) + data
        return cls.format_extended(ext_id=20, payload=payload)

    @classmethod
    def format_metadata_reject(cls, piece_index):
        # `msg_type` 2 is used to reject a metadata request
        payload = struct.pack('>B', 2) + bencodepy({'msg_type': 2, 'piece': piece_index})
        return cls.format_extended(ext_id=20, payload=payload)
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
    def parse_metadata_response_0(msg):
        ext_id, payload = Message.parse_extended(msg)
        if ext_id != 20:
            raise ValueError("Unexpected extension message for metadata")

        metadata = bencodepy.decode(payload[1:])  # Assuming `payload` contains bencoded data after the `msg_type`
        msg_type = metadata.get('msg_type')

        if msg_type == 0:
            # Handle request for a metadata piece
            piece_index = metadata.get('piece')
            # Respond with the requested piece or send reject
            return piece_index       
        else:
            raise ValueError("Unknown metadata message type")
    @staticmethod
    def parse_metadata_response_type_1(msg):
        msg_type, payload = Message.parse_extended(msg)

        metadata = bencodepy.decode(payload)  # Assuming `payload` contains bencoded data after the `msg_type`

        if msg_type == 1:
            # Handle received metadata piece
            piece_index = metadata.get('piece')
            total_size = metadata.get('total_size')
            data_start = len(payload) - len(bencodepy.encode(metadata))
            data = payload[data_start:data_start + total_size]  # Assuming data follows the first 8 bytes in the payload
            # Process received metadata piece
            return piece_index, data
        else:
            raise ValueError("Unknown metadata message type")
        
    @staticmethod
    def parse_metadata_response_type_2(msg):
        msg_type, payload = Message.parse_extended(msg)
        metadata = bencodepy.decode(payload)  # Assuming `payload` contains bencoded data after the `msg_type`
        msg_type = metadata.get('msg_type')
        if msg_type == 2:
            # Handle rejection of a metadata request
            piece_index = metadata.get('piece')
            return piece_index
            # Handle rejection
        else:
            raise ValueError("Unknown metadata message type")
    @staticmethod
    def parse_extended(msg):
        if msg.ID != MessageID.MsgExtended:
            raise ValueError(f"Expected EXTENDED (ID {MessageID.MsgExtended}), got ID {msg.ID}")
        if len(msg.Payload) < 2:
            raise ValueError(f"Payload too short. {len(msg.Payload)} < 2")

        msg_type = msg.Payload[0]
        payload = msg.Payload[1:]
        return msg_type, payload
    
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
            MessageID.MsgExtended: "Extended",
        }
        return message_names.get(self.ID, f"Unknown#{self.ID}")

    def __str__(self):
        if self.ID is None:
            return self.name()
        return f"{self.name()} [{len(self.Payload)}]"
