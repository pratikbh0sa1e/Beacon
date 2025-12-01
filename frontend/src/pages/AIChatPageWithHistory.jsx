import { useState, useRef, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import rehypeHighlight from "rehype-highlight";
import {
  Send,
  Bot,
  User,
  Loader2,
  FileText,
  AlertCircle,
  ExternalLink,
  Plus,
  History,
  Trash2,
  MessageSquare,
} from "lucide-react";
import { chatAPI } from "../services/api";
import { useChatStore } from "../stores/chatStore";
import { PageHeader } from "../components/common/PageHeader";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Card, CardContent } from "../components/ui/card";
import { Badge } from "../components/ui/badge";
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
  SheetTrigger,
} from "../components/ui/sheet";
import { ScrollArea } from "../components/ui/scroll-area";
import { toast } from "sonner";
import { formatRelativeTime } from "../utils/dateFormat";
import "highlight.js/styles/github-dark.css";

const Message = ({ message, isUser, onCitationClick }) => (
  <motion.div
    initial={{ opacity: 0, y: 20 }}
    animate={{ opacity: 1, y: 0 }}
    className={`flex gap-3 ${isUser ? "justify-end" : "justify-start"}`}
  >
    {!isUser && (
      <div className="h-8 w-8 rounded-full bg-primary/10 flex items-center justify-center flex-shrink-0">
        <Bot className="h-5 w-5 text-primary" />
      </div>
    )}
    <div className={`max-w-[80%] ${isUser ? "order-first" : ""}`}>
      <div
        className={`rounded-2xl px-4 py-3 ${
          isUser
            ? "bg-primary text-primary-foreground"
            : "glass-card border-border/50"
        }`}
      >
        {isUser ? (
          <p className="text-sm leading-relaxed whitespace-pre-wrap">
            {message.text}
          </p>
        ) : (
          <div className="prose prose-sm dark:prose-invert max-w-none prose-p:leading-relaxed prose-pre:bg-muted prose-pre:text-foreground">
            <ReactMarkdown
              remarkPlugins={[remarkGfm]}
              rehypePlugins={[rehypeHighlight]}
              components={{
                p: ({ children }) => (
                  <p className="mb-2 last:mb-0 text-sm leading-relaxed">
                    {children}
                  </p>
                ),
                ul: ({ children }) => (
                  <ul className="mb-2 ml-4 list-disc text-sm">{children}</ul>
                ),
                ol: ({ children }) => (
                  <ol className="mb-2 ml-4 list-decimal text-sm">{children}</ol>
                ),
                li: ({ children }) => (
                  <li className="mb-1 text-sm">{children}</li>
                ),
                code: ({ inline, children, ...props }) =>
                  inline ? (
                    <code
                      className="bg-muted px-1.5 py-0.5 rounded text-xs font-mono"
                      {...props}
                    >
                      {children}
                    </code>
                  ) : (
                    <code
                      className="block bg-muted p-3 rounded-lg text-xs font-mono overflow-x-auto"
                      {...props}
                    >
                      {children}
                    </code>
                  ),
                pre: ({ children }) => (
                  <pre className="bg-muted p-3 rounded-lg overflow-x-auto mb-2">
                    {children}
                  </pre>
                ),
                h1: ({ children }) => (
                  <h1 className="text-lg font-bold mb-2">{children}</h1>
                ),
                h2: ({ children }) => (
                  <h2 className="text-base font-bold mb-2">{children}</h2>
                ),
                h3: ({ children }) => (
                  <h3 className="text-sm font-bold mb-2">{children}</h3>
                ),
                blockquote: ({ children }) => (
                  <blockquote className="border-l-4 border-primary/50 pl-4 italic my-2 text-sm">
                    {children}
                  </blockquote>
                ),
                a: ({ children, href }) => (
                  <a
                    href={href}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-primary hover:underline"
                  >
                    {children}
                  </a>
                ),
                table: ({ children }) => (
                  <div className="overflow-x-auto my-2">
                    <table className="min-w-full border-collapse border border-border text-sm">
                      {children}
                    </table>
                  </div>
                ),
                th: ({ children }) => (
                  <th className="border border-border px-3 py-2 bg-muted font-semibold text-left">
                    {children}
                  </th>
                ),
                td: ({ children }) => (
                  <td className="border border-border px-3 py-2">
                    {children}
                  </td>
                ),
              }}
            >
              {message.text}
            </ReactMarkdown>
          </div>
        )}
      </div>
      {message.confidence && (
        <div className="flex items-center gap-2 mt-2 px-2">
          <Badge variant="outline" className="text-xs">
            Confidence: {(message.confidence * 100).toFixed(0)}%
          </Badge>
        </div>
      )}
      {message.citations && message.citations.length > 0 && (
        <div className="mt-3 space-y-2">
          <p className="text-xs text-muted-foreground px-2">Sources:</p>
          {message.citations.map((citation, idx) => (
            <motion.div
              key={idx}
              initial={{ opacity: 0, x: -10 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: idx * 0.1 }}
              onClick={() => onCitationClick(citation.document_id)}
              className="glass-card border-border/50 p-3 rounded-lg cursor-pointer hover:bg-accent/5 transition-colors"
            >
              <div className="flex items-start gap-2">
                <FileText className="h-4 w-4 text-primary flex-shrink-0 mt-0.5" />
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium truncate">
                    {citation.source}
                  </p>
                  <p className="text-xs text-muted-foreground">
                    Page {citation.page_number}
                  </p>
                </div>
                <ExternalLink className="h-3 w-3 text-muted-foreground flex-shrink-0 mt-0.5" />
              </div>
            </motion.div>
          ))}
        </div>
      )}
    </div>
    {isUser && (
      <div className="h-8 w-8 rounded-full bg-accent/10 flex items-center justify-center flex-shrink-0">
        <User className="h-5 w-5 text-accent" />
      </div>
    )}
  </motion.div>
);

export const AIChatPage = () => {
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [streamingMessage, setStreamingMessage] = useState(null);
  const messagesEndRef = useRef(null);
  const [historyOpen, setHistoryOpen] = useState(false);

  // Chat store
  const {
    sessions,
    currentSessionId,
    getCurrentSession,
    createSession,
    loadSession,
    addMessage,
    deleteSession,
    initializeSession,
  } = useChatStore();

  const currentSession = getCurrentSession();
  const messages = currentSession?.messages || [];

  useEffect(() => {
    initializeSession();
  }, [initializeSession]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleNewChat = () => {
    createSession();
    toast.success("New chat session created");
  };

  const handleLoadSession = (sessionId) => {
    loadSession(sessionId);
    setHistoryOpen(false);
    toast.success("Chat session loaded");
  };

  const handleDeleteSession = (sessionId, e) => {
    e.stopPropagation();
    deleteSession(sessionId);
    toast.success("Chat session deleted");
  };

  const handleSend = async () => {
    if (!input.trim() || loading) return;

    const userMessage = {
      id: Date.now(),
      text: input,
      isUser: true,
    };

    addMessage(userMessage);
    setInput("");
    setLoading(true);

    try {
      const response = await chatAPI.query(input);
      const { answer, citations, confidence } = response.data;

      const aiMessage = {
        id: Date.now() + 1,
        text: answer,
        isUser: false,
        citations: citations || [],
        confidence: confidence || 0,
      };

      addMessage(aiMessage);
    } catch (error) {
      console.error("Chat error:", error);
      const errorMessage = {
        id: Date.now() + 1,
        text: "I apologize, but I encountered an error processing your request. Please try again.",
        isUser: false,
        isError: true,
      };
      addMessage(errorMessage);
      toast.error("Failed to get AI response");
    } finally {
      setLoading(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleCitationClick = (documentId) => {
    window.open(`/documents/${documentId}`, "_blank");
  };

  return (
    <div className="h-[calc(100vh-12rem)] flex flex-col space-y-6">
      <PageHeader
        title="AI Assistant"
        description="Ask questi
};
/div>
  );>
    <</Cardt>
      rdConten </Ca>
       /div
          < </p>    
       rmation.info             ant
 rify importccurate. Vealways be at onses may noresp       AI  />
       3""h-3 w-assName=Circle cl     <Alert      ">
    gap-1items-centerx  fleund mt-2-foregroxt-mutedext-xs telassName="t       <p cv>
            </di  utton>
    </B             
4" />-4 w-Name="h class   <Send                      >

     "owgl"neon-ssName=     cla      }
     ading|| lorim() nput.tsabled={!i        di      nd}
  handleSeick={   onCl            
      <Button     
    />      
        "flex-1"sName=      clas          ading}
={lo    disabled      ess}
      PreKeyandls={heyPres       onK}
         et.value)Input(e.targ => setChange={(e)on                {input}
  value=       
       s..."ur documentt yog abouanythinme sk ="Alaceholder     p    
       put     <In       ">
  ex gap-2me="flassNacl<div             t-4">
0 porder/4-b borderborder-tassName="   <div cl
       
</div>      
    />dRef} esEnssagv ref={me   <di         }
 )          tion.div>
 /mo    <         </div>
           v>
             </di
           pan>  </s       
           inking...Th               >
       foreground"text-muted-"text-sm  className=pan<s                .div>
    motion          </          ary" />
t-prim-4 tex="h-4 wNameder2 class        <Loa             >
                           }}
           ",
     : "linear   ease                     nity,
epeat: Infi       r      
           n: 1,ratio   du                {
     transition={                      e: 360 }}
rotatnimate={{       a           div
     motion.       <        -2">
     nter gapems-celex it"fssName=<div cla             -3">
     l px-4 py2xed-ndder/50 rouer-borcard bordass-sName="gl  <div clas       >
       /div          </>
      imary" 5 text-pr"h-5 w-e=t classNam         <Bo      nk-0">
   lex-shri f-centerfyer justientx items-clerimary/10 full bg-pounded-f r"h-8 w-8sName=las  <div c          >
                "
  -3ap="flex gassName          cl}
      y: 1 }opacit={{      animate         }}
  0 ity: acl={{ op   initia    v
         otion.di  <m          age && (
  essgMin&& !stream{loading          
   sence>/AnimatePre      <}
             )      />
                ck}
 ClieCitationhandlationClick={ onCit               false}
  r={    isUse           
   ge}reamingMessasage={st       mes         .id}
  agengMess={streami    key              <Message
          (
       essage &&reamingM        {st}
      ))                />
        ck}
      itationClidleCClick={hanionatonCit          }
        ge.isUserser={messa      isU      ge}
      sage={messaes           m
       sage.id} key={mes                 ge
 <Messa        
        => (e)((messagages.mapess         {m     ence>
ePresat  <Anim       e">
   hidar-scrollbb-4 ce-y-6 m min-h-0 spaow-y-autoerfl1 ove="flex- classNam     <div     
min-h-0">x-col x fle fle"p-6 flex-1ssName=dContent cla     <Car">
   flow-hiddenverex-col o-1 flex flexer/50 flr-bordcard bordelass-"glassName=ard c

      <C />          }
  v>
        </diheet>
          </St>
     ntenheetCo        </S
      >ollArea  </Scr     >
                </div                )}
               
      ))            iv>
     </d                     >
  /div           <              </Button>
                         3" />
    w-"h-3 className=    <Trash2                                >
                     e)}
  d, on(session.iSessidleDelete{(e) => han   onClick=                    "
       shrink-0x--6 w-6 fleme="h     classNa                    con"
     "ie=         siz                   ost"
  "gh  variant=                          
    <Button               
            </div>                        </p>
                               tedAt)}
  on.updaime(sessitRelativeTforma           {                    {" "}
 ages •esses.length} magn.mess {sessio                               ground">
-forext-mutedt-xs tetexclassName="     <p                      div>
              </              </p>
                                    .title}
  ssion   {se                           ate">
    unc-medium trt-sm font"tex=sName    <p clas                      >
      shrink-0" / flex-="h-4 w-4e classNameeSquarssagMe   <                        ">
      mb-1gap-2-center ex itemssName="fl clas     <div                     >
    0"w-"flex-1 min-ame=ssN    <div cla             
           n gap-2">betweeify--start just"flex items className=       <div                           >
             `}
           }               "
   yndareco-sover:bgder horder-bor/50 bdaryg-secon      : "b                       "
 rimaryorder-p brimary/10  ? "bg-p                           ionId
 entSess== currion.id =        sess                   ${
  ion-colorsansitr trr-pointesorder cur-lg bo`p-3 roundedlassName={   c                    
   sion.id)}dSession(sesleLoa{() => hand  onClick=                    
    id}ey={session.    k                         <div
                    > (
  =ap((session)ssions.m      se              ) : (
                  </p>
                     et
      yhat history  No c                      er py-8">
ext-centound tegred-forsm text-mutext-Name="tass   <p cl             
       (=== 0 ?ength  {sessions.l                   y-2">
e-ac"splassName=iv c <d       
          ">6rem)] mt-0vh-12calc(10"h-[Name=lArea class    <Scrol          eader>
  SheetH    </          n>
  ptioescri</SheetD              ions
    sst seevious cha restore prnd   View a         >
        ptioneetDescriSh <               le>
  ry</SheetTitisto>Chat HTitleSheet    <          
    tHeader>ee         <Sh
       etContent>       <She    
   eetTrigger>  </Sh     on>
          </Butt             length})
ions. ({sessHistory                 -2" />
 "h-4 w-4 mrame=story classN   <Hi           
    outline">riant="<Button va     
           d>gger asChiletTri<She        
      ryOpen}>{setHistoOpenChange= ontoryOpen}et open={his   <She        
 Button>          </   Chat
     New
         />" mr-2-4 w-4 "hassName=lus cl   <P          e">
 nt="outlinat} variaChandleNewonClick={h    <Button >
        lex gap-2"e="f classNamdiv      <n={
          actio}
     icon={Bot  "
   gent answerstelliint and geuments our docs about yon