__author__ = 'nashok'

"""
Connection Details:
        Server host name = NASHO1
        Server listen port = 9999
above parameters should be passed as command line arguments
"""

import wx
import socket
import select
import threading
import sys
import json
import ConfigParser



class MyChatWindow(wx.Frame):
    def __init__(self, parent, title):
        wx.Frame.__init__(self, parent, title=title, size=(500, 500), pos=(530, 10), style=(wx.DEFAULT_FRAME_STYLE) & ~ (wx.RESIZE_BORDER|wx.MAXIMIZE_BOX))
        self.EnableCloseButton(False)
        self.SetBackgroundColour("grey")

        self.panel = wx.Panel(self, -1)
        self.clientList = wx.ListCtrl(self.panel, 99, name="Online Clients", pos=(20, 40), size=(140, 350), style=(wx.LC_HRULES|wx.LC_REPORT))
        self.clientList.SetBackgroundColour((204, 204, 255))
        self.clientList.InsertColumn(0, "HOST")
        self.clientList.InsertColumn(1, "IP")
        self.clientList.InsertColumn(2, "PORT")

        self.chatContentPan = wx.TextCtrl(self.panel, 1, "", wx.DLG_UNIT(self.panel, wx.Point(100, 20)), wx.DLG_UNIT(self, wx.Size(160, 150)), style=(wx.TE_MULTILINE|wx.TE_WORDWRAP|wx.TE_READONLY))
        self.chatContentPan.SetBackgroundColour((204, 204, 255))
        self.chatContentPan.SetForegroundColour((204, 0, 0))
        chatFont = wx.Font(10, wx.MODERN, wx.NORMAL, wx.NORMAL)
        self.chatContentPan.SetFont(chatFont)

        self.sendText = wx.TextCtrl(self.panel, 2, "", wx.DLG_UNIT(self.panel, wx.Point(100, 180)), wx.DLG_UNIT(self.panel, wx.Size(120, 30)), style=(wx.TE_MULTILINE|wx.TE_WORDWRAP))
        self.sendText.SetBackgroundColour((204, 204, 255))

        self.sendButton = wx.Button(self.panel, 3, "Send", wx.DLG_UNIT(self.panel, wx.Point(230, 180)), wx.DLG_UNIT(self.panel, wx.Size(30, 30)))
        self.closeButton = wx.Button(self.panel, 4, "Close Chat", wx.DLG_UNIT(self.panel, wx.Point(65, 220)), wx.DLG_UNIT(self.panel, wx.Size(60, 15)), style=wx.CENTER)
        self.clearButton = wx.Button(self.panel, 5, "Clear Chat", wx.DLG_UNIT(self.panel, wx.Point(140,220)), wx.DLG_UNIT(self.panel, wx.Size(60, 15)), style=wx.CENTER)
        self.sendButton.Bind(wx.EVT_BUTTON, self.onSend)
        self.closeButton.Bind(wx.EVT_BUTTON, self.onClose)
        self.clearButton.Bind(wx.EVT_BUTTON, self.onClear)

        self.cs = None
        self.sock_list = []
        self.chatObj = None
        self.row = 0

    def onSend(self, event):
        placeHolderText = self.sendText.GetValue()
        self.sendText.Clear()
        print placeHolderText
        self.cs.send(placeHolderText)
        self.chatContentPan.AppendText("Sent : " + placeHolderText.rstrip() + "\n\n")

    def onClose(self, event):
        if self.cs != None:
            self.cs.close()
        self.Destroy()
        sys.exit(0)

    def onClear(self, event):
        self.chatContentPan.Clear()
        event.Skip()

    def setAttributes(self, s, ccobj):
        self.cs = s
        self.chatObj = ccobj
        print "Called from client thread"

    def removeClientFromList(self, rmclient):
        hostname = socket.gethostbyaddr(rmclient[0])
        print hostname[0].split('.')[0]
        for row in range(self.clientList.GetItemCount()):
            print "row -> " + str(row)
            if hostname[0].split('.')[0] == self.clientList.GetItem(row, 0).GetText() and str(rmclient[0]) == self.clientList.GetItem(row, 1).GetText() and str(rmclient[1]) == self.clientList.GetItem(row, 2).GetText():
                print self.clientList.GetItem(row, 0).GetText()
                print self.clientList.GetItem(row, 1).GetText()
                self.clientList.DeleteItem(row)
                self.row = self.row - 1
                break
        if not self.clientList.GetItemCount():
            if self.sendButton.IsEnabled():
                self.sendButton.Disable()

    def addClientToList(self, addr):
        hostname = socket.gethostbyaddr(addr[0])
        print hostname[0].split('.')[0]
        pos = self.clientList.InsertItem(self.row, hostname[0].split('.')[0])
        self.clientList.SetItem(pos, 1, str(addr[0]))
        self.clientList.SetItem(pos, 2, str(addr[1]))
        self.row = self.row + 1

class MyApp(wx.App):
    def OnInit(self):
        self.frame = MyChatWindow(parent=None, title="My Client - 3",)
        chatClient = MyChatClient(self.frame)
        if self.frame.sendButton.IsEnabled():
            self.frame.sendButton.Disable()
        self.frame.Show(True)
        return True

    def MainLoop(self):
        wx.PyApp.MainLoop(self)

class MyChatClient(object):
    def __init__(self, fmobj):
        self.fmobj = fmobj
        self.SOCK_LIST = []
        self.RECV_BUFFER = 4096
        self.clientsDict = {}

        ct = threading.Thread(target=ClientBee, name='ClinetThread', args=(self.fmobj, self))
        ct.start()

    def getOnlineClients(self):
        return self.clientsDict

    def addOnlineClients(self, soc, addr):
        self.clientsDict[soc] = addr
        print "In add client -->"
        print self.clientsDict

    def removeOfflineClients(self, soc, addr):
        if soc in self.clientsDict.keys():
            if self.clientsDict[soc] == addr:
                self.clientsDict.__delitem__(soc)
        print "In remove clients -->"
        print self.clientsDict

    def ReadAndParseConfig(self):
        optiondict = {}
        Config = ConfigParser.ConfigParser()
        Config.read("client.cfg")
        sections = Config.sections()
        for section in sections:
            options = Config.options(section)
            for option in options:
                optiondict[option] =  Config.get(section, option)
        return optiondict

def ClientBee(fmobj, ccobj):
    server_details = ccobj.ReadAndParseConfig()
    print server_details
    if 'serverhost' in server_details.keys():
        if 'serverport' in server_details.keys():
            host = socket.gethostbyname(server_details['serverhost'])
            port = int(server_details['serverport'])
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(2)
    else:
        print "Pleae provide required server details in client.cfg file\nFormat:\n\tserverhost: <serverhost name>\n\tserverport: <serverport>"
        fmobj.Destroy()
        sys.exit()

    # connect to remote host
    try:
        print "before conn --> %s" %(s)
        s.connect((host, port))
        print "Client-1 connected as --> %s" %(s.getsockopt)
    except:
        print 'Unable to connect'
        fmobj.Destroy()
        sys.exit(0)

    print 'Connected to remote host. You can start sending messages'
    fmobj.setAttributes(s, ccobj)

    while 1:
        socket_list = [s]

        # Get the list sockets which are readable
        try:
            print "Before select in client"
            read_sockets, write_sockets, error_sockets = select.select(socket_list , [], [])
            for sock in read_sockets:
                if sock == s:
                    # incoming message from remote server, s
                    data = sock.recv(ccobj.RECV_BUFFER)
                    if not data:
                        print '\nDisconnected from chat server'
                        sock.close()
                        fmobj.Destroy()
                        sys.exit()
                    else :
                        try:
                            tempDict = json.loads(data)
                            print "\nJsonString received"
                            print tempDict
                            for key in tempDict.keys():
                                temp = ccobj.getOnlineClients()
                                if key in temp.keys():
                                    if temp[key] == tempDict[key]:
                                        fmobj.removeClientFromList(temp[key])
                                        ccobj.removeOfflineClients(key, temp[key])
                                else:
                                    ccobj.addOnlineClients(key, tempDict[key])
                                    fmobj.addClientToList(tempDict[key])
                                    #pos = fmobj.clientList.InsertStringItem(col, str(tempDict[key][0]))
                                    #fmobj.clientList.SetStringItem(pos, 1, str(tempDict[key][1]))
                                    if not fmobj.sendButton.IsEnabled():
                                        fmobj.sendButton.Enable()
                        except ValueError, e:
                            print "\nNormal string received"
                            fmobj.chatContentPan.AppendText("Received : " + data.rstrip() + "\n\n")
                            sys.stdout.write(data)
                fmobj.setAttributes(s, ccobj)
        except socket.error:
            s.close()
            break



def main():
    app = MyApp(0)
    app.MainLoop()

if __name__ == '__main__':
    main()