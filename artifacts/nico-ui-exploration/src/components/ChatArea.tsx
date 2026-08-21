import React, { useState, useEffect, useRef } from 'react';
import { Send, Mic, Image as ImageIcon, Sparkles, Plus } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

interface MessageType {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  isTyping?: boolean;
}

export function ChatArea() {
  const [messages, setMessages] = useState<MessageType[]>([
    {
      id: '1',
      role: 'assistant',
      content: 'Selam! Ben Nico. Bugün nasıl hissediyorsun, neler yapıyorsun?'
    },
    {
      id: '2',
      role: 'user',
      content: 'Of ya, bugün işler hiç bitmedi falan, çok yoruldum uff.'
    },
    {
      id: '3',
      role: 'assistant',
      content: 'Kıyamam ya, bazen her şey üst üste gelir öyle. Derin bir nefes al önce. 🧘‍♂️ Belki akşam kendine güzel bir kahve ya da çay yapıp, sadece 10 dakika hiçbir şey yapmadan oturursun? Sana iyi gelebilecek sakin bir şarkı açmamı ister misin?'
    }
  ]);
  const [inputValue, setInputValue] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isTyping]);

  const handleSend = (e?: React.FormEvent) => {
    e?.preventDefault();
    if (!inputValue.trim()) return;

    const newUserMsg: MessageType = {
      id: Date.now().toString(),
      role: 'user',
      content: inputValue
    };

    setMessages(prev => [...prev, newUserMsg]);
    setInputValue('');
    setIsTyping(true);

    // Simulate AI response
    setTimeout(() => {
      setIsTyping(false);
      const newAiMsg: MessageType = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: 'Anlıyorum. Bazen "uff" deyip geçmek en iyisidir. Biraz daha anlatmak ister misin, yoksa kafanı dağıtacak başka bir şeyden mi bahsedelim?'
      };
      setMessages(prev => [...prev, newAiMsg]);
    }, 2500);
  };

  return (
    <div className="glass-panel h-full w-full rounded-3xl flex flex-col overflow-hidden relative shadow-[0_12px_40px_0_rgba(0,0,0,0.03)] border-white/50">
      
      {/* Chat Header Background Accent */}
      <div className="absolute top-0 left-0 right-0 h-32 bg-gradient-to-b from-white/40 to-transparent pointer-events-none z-0" />

      {/* Messages Area */}
      <div className="flex-1 overflow-y-auto p-4 md:p-8 space-y-6 z-10 scroll-smooth">
        <AnimatePresence initial={false}>
          {messages.map((msg) => (
            <MessageBubble key={msg.id} message={msg} />
          ))}
          {isTyping && (
            <motion.div
              initial={{ opacity: 0, y: 10, scale: 0.95 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              exit={{ opacity: 0, scale: 0.95, transition: { duration: 0.2 } }}
              className="flex items-end gap-3 w-full max-w-[85%] md:max-w-2xl"
            >
              <div className="w-8 h-8 rounded-full bg-gradient-to-br from-indigo-100 to-blue-50 border border-blue-200/50 flex items-center justify-center shadow-sm shrink-0">
                <Sparkles size={14} className="text-blue-500" />
              </div>
              <div className="glass-message-ai rounded-2xl rounded-bl-sm p-4 relative overflow-hidden group">
                <div className="absolute inset-0 bg-white/20 opacity-0 group-hover:opacity-100 transition-opacity duration-300"></div>
                <div className="flex gap-1.5 items-center h-5">
                  <motion.div
                    className="w-2 h-2 rounded-full bg-blue-400"
                    animate={{ y: [0, -5, 0] }}
                    transition={{ repeat: Infinity, duration: 0.6, ease: 'easeInOut' }}
                  />
                  <motion.div
                    className="w-2 h-2 rounded-full bg-blue-400"
                    animate={{ y: [0, -5, 0] }}
                    transition={{ repeat: Infinity, duration: 0.6, ease: 'easeInOut', delay: 0.2 }}
                  />
                  <motion.div
                    className="w-2 h-2 rounded-full bg-blue-400"
                    animate={{ y: [0, -5, 0] }}
                    transition={{ repeat: Infinity, duration: 0.6, ease: 'easeInOut', delay: 0.4 }}
                  />
                </div>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
        <div ref={messagesEndRef} className="h-2" />
      </div>

      {/* Input Area */}
      <div className="p-4 md:p-6 shrink-0 z-10 relative">
        <div className="absolute top-0 left-0 right-0 h-px bg-gradient-to-r from-transparent via-white/50 to-transparent" />
        
        <form onSubmit={handleSend} className="relative group max-w-4xl mx-auto">
          <div className="absolute -inset-1 bg-gradient-to-r from-blue-200/30 to-indigo-200/30 rounded-[2rem] blur opacity-50 group-hover:opacity-100 transition duration-500" />
          
          <div className="relative flex items-end gap-2 bg-white/70 backdrop-blur-xl border border-white/60 p-2 rounded-[1.75rem] shadow-sm focus-within:ring-2 focus-within:ring-blue-400/30 focus-within:bg-white/80 transition-all duration-300">
            
            <button type="button" className="p-3 text-slate-400 hover:text-blue-500 hover:bg-blue-50 rounded-full transition-colors shrink-0">
              <Plus size={20} />
            </button>
            
            <textarea
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                  e.preventDefault();
                  handleSend();
                }
              }}
              placeholder="Nico'ya bir şeyler söyle..."
              className="flex-1 max-h-32 min-h-[44px] bg-transparent resize-none outline-none py-3 text-slate-700 placeholder:text-slate-400 scrollbar-hide text-[15px] leading-relaxed"
              rows={1}
            />
            
            <div className="flex items-center gap-1 shrink-0">
              {!inputValue.trim() ? (
                <button type="button" className="p-3 text-slate-400 hover:text-slate-600 hover:bg-white/50 rounded-full transition-colors">
                  <Mic size={20} />
                </button>
              ) : (
                <button 
                  type="submit"
                  className="p-3 bg-blue-500 text-white hover:bg-blue-600 hover:scale-105 rounded-full transition-all duration-200 shadow-md shadow-blue-500/20"
                >
                  <Send size={18} className="translate-x-[1px] translate-y-[-1px]" />
                </button>
              )}
            </div>
          </div>
        </form>
        <div className="text-center mt-3">
          <span className="text-[11px] text-slate-400 font-medium">Nico hata yapabilir. Lütfen önemli bilgileri kontrol et.</span>
        </div>
      </div>
    </div>
  );
}

const MessageBubble = ({ message }: { message: MessageType }) => {
  const isUser = message.role === 'user';
  
  return (
    <motion.div
      initial={{ opacity: 0, y: 10, scale: 0.95 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      className={`flex items-end gap-3 w-full ${isUser ? 'justify-end' : 'justify-start'}`}
    >
      {!isUser && (
        <div className="w-8 h-8 rounded-full bg-gradient-to-br from-indigo-100 to-blue-50 border border-blue-200/50 flex items-center justify-center shadow-sm shrink-0 z-10">
          <Sparkles size={14} className="text-blue-500" />
        </div>
      )}
      
      <div 
        className={`max-w-[85%] md:max-w-2xl px-5 py-4 text-[15px] leading-relaxed relative overflow-hidden group shadow-sm
          ${isUser 
            ? 'glass-message-user rounded-2xl rounded-br-sm text-slate-800' 
            : 'glass-message-ai rounded-2xl rounded-bl-sm text-slate-800'
          }
        `}
      >
        <div className="absolute inset-0 bg-white/20 opacity-0 group-hover:opacity-100 transition-opacity duration-300 pointer-events-none"></div>
        <p className="relative z-10 whitespace-pre-wrap">{message.content}</p>
      </div>
      
      {isUser && (
        <div className="w-8 h-8 rounded-full bg-slate-200/50 border border-white/50 backdrop-blur-md flex items-center justify-center text-slate-500 font-bold text-xs shadow-sm shrink-0 z-10">
          M
        </div>
      )}
    </motion.div>
  );
}
