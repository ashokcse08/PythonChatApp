# PythonChatApp
This is python based group chat application.

1. Server must be running.
2. To start the chat from any client, there must be more than one client connected to the server.
3. To run the application, you should have python 2.7.x installed and wxPython module installed on top of python installation. pip install wxPython will install the latest wxPython package for you.
4. The client code can be copied to new files to make the new clients. Just to differentiate, you can change the client window name in the ChatClient python code - line number : 101 (self.frame = MyChatWindow(parent=None, title="My Client - 3",))