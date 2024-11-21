from pythonosc.udp_client import SimpleUDPClient

class VRChatVoiceManager:
    def __init__(self, ip="127.0.0.1", port=9001):
        self.osc_client = SimpleUDPClient(ip, port)
        
    def send_voice_command(self, text):
        # Send TTS commands via OSC
        self.osc_client.send_message("/avatar/parameters/Speech", text)
        
    def send_expression(self, expression_type):
        # Control avatar expressions
        self.osc_client.send_message("/avatar/parameters/Expression", expression_type)
