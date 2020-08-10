import re

from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5 import Qsci
from PyQt5.Qsci import QsciScintilla, QsciLexerCustom


class SmsTextWidget(QsciScintilla):
    ARROW_MARKER_NUM = 8
    line_ending = "\n"
    findText = pyqtSignal(str)

    def __init__(self, parent=None, autocompletions=None):
        super(SmsTextWidget, self).__init__(parent)

        # Set the default font
        font = QFont()
        font.setFamily('Consolas')
        font.setFixedPitch(True)
        font.setPointSize(9)
        self.setFont(font)
        self.setMarginsFont(font)

        """
        Customization - GENERAL
        """
        self.lexer = SmsLexer(self)
        # Disable the lexer
        self.setLexer(self.lexer)
        # Set the encoding to UTF-8
        self.setUtf8(True)
        # Set the End-Of-Line character to Unix style ('\n')
        #self.setEolMode(QsciScintilla.EolUnix)
        # Make End-Of-Line characters visible
        #self.setEolVisibility(True)
        # Set the zoom factor, the factor is in points.
        self.zoomTo(3)

        """
        Customization - LINE WRAPPING
        """
        # Set the text wrapping mode to word wrap
        self.setWrapMode(QsciScintilla.WrapWord)
        # Set the text wrapping mode visual indication
        self.setWrapVisualFlags(QsciScintilla.WrapFlagInMargin)
        # Set the text wrapping to indent the wrapped lines
        self.setWrapIndentMode(QsciScintilla.WrapIndentSame)

        """
        Customization - EDGE MARKER
        """
        # Set the edge marker's position and set it to color the background
        # when a line goes over the limit of 50 characters
        self.setEdgeMode(QsciScintilla.EdgeBackground)
        self.setEdgeColumn(2000)
        edge_color = caret_fg_color = QColor("#1fff0000")
        self.setEdgeColor(edge_color)
        # Add a long line that will display the edge marker coloring
        #self.append("\nSome long line that will display the edge marker's functionality.")

        """
        Customization - INDENTATION
        """
        # Set indentation with spaces instead of tabs
        self.setIndentationsUseTabs(False)
        # Set the tab width to 4 spaces
        self.setTabWidth(4)
        # Set tab indent mode, see the 3.3.4 chapter in QSciDocs
        # for a detailed explanation
        self.setTabIndents(True)
        # Set autoindentation mode to maintain the indentation
        # level of the previous line (the editor's lexer HAS
        # to be disabled)
        self.setAutoIndent(True)
        # Make the backspace jump back to the tab width guides
        # instead of deleting one character, but only when
        # there are ONLY whitespaces on the left side of the
        # cursor
        self.setBackspaceUnindents(True)
        # Set indentation guides to be visible
        self.setIndentationGuides(True)

        """
        Customization - CARET (the blinking cursor indicator)
        """
        # # Set the caret color to red
        # caret_fg_color = QColor("#ffff0000")
        # self.setCaretForegroundColor(caret_fg_color)
        # # Enable and set the caret line background color to slightly transparent blue
        # self.setCaretLineVisible(True)
        # caret_bg_color = QColor("#7f0000ff")
        # self.setCaretLineBackgroundColor(caret_bg_color)
        # # Set the caret width of 4 pixels
        # self.setCaretWidth(4)

        """
        Customization - AUTOCOMPLETION (Partially usable without a lexer)
        """

        self.__api = Qsci.QsciAPIs(self.lexer)
        autocompletions = [
            "test_autocompletion",
            "add(int arg_1, float arg_2) Add two integers together",
            "subtract(int arg_1, test arg_2)",
            "subtract(float arg_1, float arg_2)",
            "subtract(test arg_1, test arg_2)",
            "divide(float div_1, float div_2)",
            "some_func(arg_3)",
            "\\$ABC$",
        ]
        for ac in autocompletions:
            self.__api.add(ac)
        self.__api.prepare()

        # Set the autocompletions to case INsensitive
        self.setAutoCompletionCaseSensitivity(False)
        # Set the autocompletion to not replace the word to the right of the cursor
        self.setAutoCompletionReplaceWord(False)
        # Set the autocompletion source to be the words in the
        # document
        self.setAutoCompletionSource(Qsci.QsciScintilla.AcsAPIs)
        # Set the autocompletion dialog to appear as soon as 1 character is typed
        self.setAutoCompletionThreshold(1)


    def setAutocompletions(self, autocompletions):
        for ac in autocompletions:
            self.__api.add(ac)
        self.__api.add('ads')
        self.__api.prepare()
        self.setAutoCompletionSource(Qsci.QsciScintilla.AcsAPIs)
        self.lexer.setVariable(autocompletions)


class SmsLexer(QsciLexerCustom):
    def __init__(self, parent):
        super(SmsLexer, self).__init__(parent)
        self.variable_list = []

        # Default text settings
        # ----------------------
        self.setDefaultColor(QColor("#ff000000"))
        self.setDefaultPaper(QColor("#ffffffff"))
        self.setDefaultFont(QFont("Consolas", 9))

        # Initialize colors per style
        # ----------------------------
        self.setColor(QColor("#ff000000"), 0)   # Style 0: black
        self.setColor(QColor("#ff7f0000"), 1)   # Style 1: red
        self.setColor(QColor("#ff0000bf"), 2)   # Style 2: blue
        self.setColor(QColor("#ff007f00"), 3)   # Style 3: green

        # Initialize paper colors per style
        # ----------------------------------
        self.setPaper(QColor("#ffffffff"), 0)           # Style 0: white
        self.setPaper(QColor(QColor(255, 215, 0)), 1)   # Style 1: white
        self.setPaper(QColor("#ffffffff"), 2)           # Style 2: white
        self.setPaper(QColor("#ffffffff"), 3)           # Style 3: white

        # Initialize fonts per style
        # ---------------------------
        self.setFont(QFont("Consolas", 9, weight=QFont.Bold), 0)   # Style 0: Consolas 11pt
        self.setFont(QFont("Consolas", 9, weight=QFont.Bold), 1)   # Style 1: Consolas 11pt
        self.setFont(QFont("Consolas", 9, weight=QFont.Bold), 2)   # Style 2: Consolas 11pt
        self.setFont(QFont("Consolas", 9, weight=QFont.Bold), 3)   # Style 3: Consolas 11pt

    def setVariable(self, variable_list):
        for variable_id in variable_list:
            self.variable_list.append(variable_id)

    def language(self):
        return "SimpleLanguage"

    def description(self, style):
        if style == 0:
            return "myStyle_0"
        elif style == 1:
            return "myStyle_1"
        elif style == 2:
            return "myStyle_2"
        elif style == 3:
            return "myStyle_3"
        ###
        return ""

    def styleText(self, start, end):
        # 1. Initialize the styling procedure
        # ------------------------------------
        self.startStyling(start)

        # 2. Slice out a part from the text
        # ----------------------------------
        text = self.parent().text()[start:end]

        # 3. Tokenize the text
        # ---------------------
        p = re.compile(r"[*]\/|\/[*]|\S+|\w+|\W")

        # 'token_list' is a list of tuples: (token_name, token_len)
        token_list_tmp = [[token, len(bytearray(token, "utf-8"))] for token in p.findall(text)]

        token_list = []

        for ix, token in enumerate(token_list_tmp):
            #     print(token)
            variable_p = re.compile(r'\$\w+\$|\w+|\S')
            variable_token_list = [[variable_token, len(bytearray(variable_token, "utf-8"))] for variable_token in
                                   variable_p.findall(token[0])]

            if variable_token_list:
                #print(token, variable_token_list)
                for variable_token in variable_token_list:
                    token_list.append(variable_token)
            else:
                token_list.append(token)

        # print(token_list)
        # 4. Style the text
        # ------------------
        # 4.1 Check if multiline comment
        multiline_comm_flag = False
        editor = self.parent()
        if start > 0:
            previous_style_nr = editor.SendScintilla(editor.SCI_GETSTYLEAT, start - 1)
            if previous_style_nr == 3:
                multiline_comm_flag = True
        # 4.2 Style the text in a loop
        for i, token in enumerate(token_list):
            if multiline_comm_flag:
                self.setStyling(token[1], 3)
                if token[0] == "*/":
                    multiline_comm_flag = False
            else:
                variable_p = re.compile(r'\$\w+\$')
                variable_token_list = [(variable_token, len(bytearray(variable_token, "utf-8"))) for variable_token in variable_p.findall(token[0])]
                if variable_token_list:
                    # Red style
                    for variable_token in variable_token_list:
                        #print(variable_token[0], variable_token[1])
                        if variable_token[0] in self.variable_list:
                            self.setStyling(variable_token[1], 1)
                # elif token[0] in ["for", "while", "return", "int", "include"]:
                #     # Red style
                #     self.setStyling(token[1], 1)
                # elif token[0] in ["(", ")", "{", "}", "[", "]", "#"]:
                #     # Blue style
                #     self.setStyling(token[1], 2)
                # elif token[0] == "/*":
                #     multiline_comm_flag = True
                #     self.setStyling(token[1], 3)
                else:
                    # Default style
                    self.setStyling(token[1], 0)