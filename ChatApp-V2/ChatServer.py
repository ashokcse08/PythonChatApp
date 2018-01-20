__author__ = 'nashok'

import wx
import socket
import select
import threading
import sys
from json import dumps


class MyChatWindow(wx.Frame):
    def __init__(self, parent, title):
        wx.Frame.__init__(self, parent, title=title, size=(500, 500), pos=(1, 1), style=(wx.DEFAULT_FRAME_STYLE) & ~ (wx.RESIZE_BORDER|wx.MAXIMIZE_BOX))
        self.EnableCloseButton(False)
        self.SetBackgroundColour("#4f5049")

        self.panel = wx.Panel(self, -1)
        #self.panel.SetBackgroundColour("#4f5049")
        self.clientList = wx.ListCtrl(self.panel, 99, name="Connected Clients", pos=(20, 40), size=(140, 350), style=(wx.LC_HRULES|wx.LC_REPORT))
        self.clientList.InsertColumn(0, "HOST")
        self.clientList.InsertColumn(1, "IP")
        self.clientList.InsertColumn(2, "PORT")

        self.chatContentPan = wx.TextCtrl(self.panel, 1, "", pos=wx.DLG_UNIT(self.panel, wx.Point(100, 20)), size=wx.DLG_UNIT(self, wx.Size(160, 150)), style=(wx.TE_MULTILINE|wx.TE_WORDWRAP|wx.TE_READONLY))

        self.sendText = wx.TextCtrl(self.panel, 2, "", wx.DLG_UNIT(self.panel, wx.Point(100, 180)), wx.DLG_UNIT(self.panel, wx.Size(120, 30)), style=(wx.TE_MULTILINE|wx.TE_WORDWRAP))
        self.sendButton = wx.Button(self.panel, 3, "Send", wx.DLG_UNIT(self.panel, wx.Point(230, 180)), wx.DLG_UNIT(self.panel, wx.Size(30, 30)))
        self.StopButton = wx.Button(self.panel, 4, "Stop SERVER", wx.DLG_UNIT(self.panel, wx.Point(65, 220)), wx.DLG_UNIT(self.panel, wx.Size(60, 15)), style=wx.CENTER)

        """
        # Set sizer for the frame, so we can change frame size to match widgets
        self.windowSizer = wx.BoxSizer()
        self.windowSizer.Add(self.panel, 1, wx.ALL | wx.EXPAND)
        # Set sizer for the panel content
        self.sizer = wx.GridBagSizer(5, 5)
        self.sizer.Add(self.StopButton, (2, 0), (1, 2), flag=wx.EXPAND)
        # Set simple sizer for a nice border
        self.border = wx.BoxSizer()
        self.border.Add(self.sizer, 1, wx.ALL | wx.EXPAND, 5)

        # Use the sizers
        #self.panel.SetSizerAndFit(self.border)
        #self.SetSizerAndFit(self.windowSizer)
        """

        self.sendButton.Bind(wx.EVT_BUTTON, self.onSend)
        self.StopButton.Bind(wx.EVT_BUTTON, self.onClose)

        self.ss = None
        self.sock_list = []
        self.chatObj = None
        self.char_serv_thread = None
        self.terminate = False
        self.row = 0

    def onSend(self, event):
        placeHolderText = self.sendText.GetValue()
        self.sendText.Clear()
        print placeHolderText

        # Broadcasting server message to all connected clients
        self.chatObj.broadcast(self.ss, placeHolderText.rstrip() + "\n", None, True)
        self.chatContentPan.AppendText("Sent : " + placeHolderText.rstrip() + "\n")

    def onClose(self, event):
        print "Stopping Server"
        if self.sock_list != [] and self.sock_list != None:
            for soc in self.sock_list:
                soc.close()
                print "after closing soc" + str(soc)
                if soc == self.ss:
                    self.ss.close()
                    print "closed server socket also"
        self.terminate = True
        self.char_serv_thread.join()
        self.Destroy()
        sys.exit(0)

    def removeClientFromList(self, rmclient):
        hostname = socket.gethostbyaddr(rmclient[0])
        print hostname[0].split('.')[0]
        for row in range(self.clientList.GetItemCount()):
            print "row -> " + str(row)
            if hostname[0].split('.')[0] == self.clientList.GetItem(row, 0).GetText() and str(rmclient[0]) == self.clientList.GetItem(row, 1).GetText() and str(rmclient[1]) == self.clientList.GetItem(row, 2).GetText():
                print self.clientList.GetItem(row, 0).GetText()
                print self.clientList.GetItem(row, 1).GetText()
                print self.clientList.GetItem(row, 2).GetText()
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

    def setAttributes(self, ss = None, rlist = None, csobj = None, cst = None):
        self.ss = ss
        self.sock_list = rlist
        self.chatObj = csobj
        if self.char_serv_thread == None:
            self.char_serv_thread = cst
        print "Called from server thread"


class MyChatServer(object):
    def __init__(self, fmobj, port):
        self.fmobj = fmobj # Main window frame object
        self.host = socket.gethostname()
        print "Host name = " + self.host
        self.port = port
        self.SOCK_LIST = []
        self.RECV_BUFFER = 4096
        self.startServer()
        self.st = None # variable to hold the thread object
        self.clientsDict = {}

    def startServer(self):
        self.server_socket = socket.socket(family=socket.AF_INET, type=socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((socket.gethostbyname(self.host), self.port))

        self.server_socket.listen(5)
        self.SOCK_LIST.append(self.server_socket)
        if self.server_socket:
            print "server started %s" %str(self.server_socket)
            print socket.gethostbyname(self.host), self.port
            print "Connection done"

        self.st = threading.Thread(target=ChatBee, name='ServerThread', args=(self.fmobj, self, self.server_socket, self.SOCK_LIST, [], [], 0))
        self.st.start()
        self.fmobj.setAttributes(cst=self.st)

    def broadcast(self, serv_socket, message, sock=None, fromServer=False):
        if fromServer and sock == None:
            for socket in self.SOCK_LIST:
                if socket!= serv_socket:
                    try:
                        print "In Broadcast from server to socket : %s , and message : %s" %(str(socket), message)
                        socket.send(message)
                    except:
                        # broken socket connection
                        print "In except of broadcast : Socket is broken and is closed --> " + str(socket)
                        socket.close()
                        # broken socket, remove it
                        if socket in self.SOCK_LIST:
                            self.SOCK_LIST.remove(socket)
        else:
            for socket in self.SOCK_LIST:
                # send the message only to peer
                if socket != serv_socket and socket != sock:
                    try:
                        print "In Broadcast to socket : %s , and message : %s" %(str(socket), message)
                        socket.send(message)
                    except:
                        # broken socket connection
                        socket.close()
                        # broken socket, remove it
                        if socket in self.SOCK_LIST:
                            self.SOCK_LIST.remove(socket)

    def setSocAttributes(self, soclist):
        self.SOCK_LIST = soclist

    def getOnlineClients(self):
        return self.clientsDict

    def addOnlineClientsToDict(self, soc, addr):
        self.clientsDict[soc] = addr
        print "In add client -->"
        print self.clientsDict

    def removeOfflineClients(self, soc, addr):
        if soc in self.clientsDict.keys():
            if self.clientsDict[soc] == addr:
                self.clientsDict.__delitem__(soc)
        print "In remove clients -->"
        print self.clientsDict


class MyApp(wx.App):
    def OnInit(self):
        self.frame = MyChatWindow(parent=None, title="My Server",)
        self.chatServer = MyChatServer(self.frame, 55556)
        if self.frame.sendButton.IsEnabled():
            self.frame.sendButton.Disable()
        self.frame.Show(True)
        return True

    def MainLoop(self):
        wx.PyApp.MainLoop(self)


def ChatBee(fmobj, csobj, ss, rlist, wlist, xlist, to):
    col = 0
    clientsDict = {}
    tempDict = {}
    while 1:
        try:
            rl, wl, erl = select.select(rlist, wlist, xlist, to)
            for soc in rl:
                if soc == ss:
                    socfd, addr = ss.accept()
                    rlist.append(socfd)
                    csobj.setSocAttributes(rlist)
                    clientsDict = csobj.getOnlineClients()
                    if clientsDict != {}:
                        socfd.send(dumps(clientsDict))
                    csobj.addOnlineClientsToDict(str(socfd), addr)
                    print "New conncetion from %s --> %s" % (str(addr), str(socfd))
                    if not fmobj.sendButton.IsEnabled():
                        fmobj.sendButton.Enable()
                    fmobj.addClientToList(addr)
                    # pos = fmobj.clientList.InsertStringItem(col, str(addr[0]))
                    # fmobj.clientList.SetStringItem(pos, 1, str(addr[1]))
                    col = col + 1
                    tempDict[str(socfd)] = addr
                    # csobj.broadcast(ss, "[%s] entered our chatting room\n" % str(addr), socfd)
                    csobj.broadcast(ss, dumps(tempDict), socfd)
                    tempDict.popitem()
                    fmobj.chatContentPan.AppendText("connected to : " + str(addr).rstrip() + "\n")

                else:
                    try:
                        data = soc.recv(csobj.RECV_BUFFER)
                        if data:
                            csobj.broadcast(ss, "\r" + '[' + str(soc.getpeername()) + '] ' + data.rstrip(), soc)
                            fmobj.chatContentPan.AppendText("Received : " + data.rstrip() + "\n")
                        else:
                            # remove the socket that's broken
                            if soc in rlist:
                                soc.close()
                                print str(soc) + " is closed"
                                rlist.remove(soc)
                                csobj.setSocAttributes(rlist)
                            clientsDict = csobj.getOnlineClients()
                            tempDict[str(soc)] = clientsDict[str(soc)]
                            csobj.broadcast(ss, dumps(tempDict), None, True)
                            tempDict = {}
                            fmobj.chatContentPan.AppendText("Client (%s) is offline\n" % str(clientsDict[str(soc)]))
                            fmobj.removeClientFromList(clientsDict[str(soc)])
                            csobj.removeOfflineClients(str(soc), clientsDict[str(soc)])

                    except socket.error as error:
                        soc.close()
                        rlist.remove(soc)
                        csobj.setSocAttributes(rlist)
                        print "last before --> " + str(error)
                fmobj.setAttributes(ss, rlist, csobj)
            if fmobj.terminate: ## Facilitates the server thread to terminate before any client is connected
                break
        except socket.error:
            for socfd in rlist:
                socfd.close()
            print "Server Stopped"
            break


def main():
    app = MyApp(0)
    app.MainLoop()

if __name__ == '__main__':
    main()