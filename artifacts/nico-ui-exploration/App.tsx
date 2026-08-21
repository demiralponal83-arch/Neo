import React, { useState, useRef, useEffect } from 'react';
import { Send, Menu, Plus } from 'lucide-react';
import { Button } from './components/ui/button';
import { Input } from './components/ui/input';
import { ScrollArea } from './components/ui/scroll-area';
import { Avatar, AvatarFallback } from './components/ui/avatar';
import { Sheet, SheetContent, SheetTrigger } from './components/ui/sheet';

interface Message {
  id: number;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
}

interface Conversation {
  id: number;
  title: string;
  preview: string;
  timestamp: Date;
}

const MOCK_CONVERSATIONS: Conversation[] = [
  { id: 1, title: 'İş toplantısı notları', preview: 'Yarınki sunum için ana başlıkları özetler misin?', timestamp: new Date(Date.now() - 2 * 60 * 60 * 1000) },
  { id: 2, title: 'Yemek tarifi', preview: 'Pratik bir pilav tarifi lazım, uff bugün çok yorgunum', timestamp: new Date(Date.now() - 5 * 60 * 60 * 1000) },
  { id: 3, title: 'Kod yardımı', preview: 'React state management konusunda tavsiye', timestamp: new Date(Date.now() - 24 * 60 * 60 * 1000) },
  { id: 4, title: 'Seyahat planı', preview: 'Karadeniz turu için güzergah önerisi falan', timestamp: new Date(Date.now() - 3 * 24 * 60 * 60 * 1000) },
];

const INITIAL_MESSAGES: Message[] = [
  { id: 1, role: 'user', content: 'Merhaba Nico! Bugün bana yardımcı olabilir misin?', timestamp: new Date(Date.now() - 10 * 60 * 1000) },
  { id: 2, role: 'assistant', content: 'Tabii ki! Ne konuda yardıma ihtiyacın var? Sana nasıl destek olabilirim?', timestamp: new Date(Date.now() - 9 * 60 * 1000) },
  { id: 3, role: 'user', content: 'Bugünkü toplantım için ana konuları özetlemem lazım. Elimde bir sürü not var ama of, nereden başlayacağımı bilemedim.', timestamp: new Date(Date.now() - 8 * 60 * 1000) },
  { id: 4, role: 'assistant', content: 'Hiç sorun değil, hadi birlikte bakalım! Notlarını bana gönderebilirsin, ben senin için ana başlıkları çıkarır ve özetlerim. Böylece toplantıda kafan daha rahat olur 😊', timestamp: new Date(Date.now() - 7 * 60 * 1000) },
];

function formatTimestamp(date: Date): string {
  const now = new Date();
  const diff = now.getTime() - date.getTime();
  const hours = Math.floor(diff / (1000 * 60 * 60));
  const days = Math.floor(hours / 24);

  if (hours < 1) return 'Şimdi';
  if (hours < 24) return `${hours} saat önce`;
  if (days === 1) return 'Dün';
  return `${days} gün önce`;
}

function App() {
  const [messages, setMessages] = useState<Message[]>(INITIAL_MESSAGES);
  const [input, setInput] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const [conversations] = useState<Conversation[]>(MOCK_CONVERSATIONS);
  const scrollRef = useRef<HTMLDivElement>(null);
  const [userName] = useState('Ayşe');

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages, isTyping]);

  const handleSend = () => {
    if (!input.trim()) return;

    const userMessage: Message = {
      id: messages.length + 1,
      role: 'user',
      content: input,
      timestamp: new Date(),
    };

    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setIsTyping(true);

    setTimeout(() => {
      const assistantMessage: Message = {
        id: messages.length + 2,
        role: 'assistant',
        content: 'Anladım! Hemen üzerinde çalışıyorum. Biraz sabret, çok güzel bir özet hazırlayacağım 🚀',
        timestamp: new Date(),
      };
      setMessages(prev => [...prev, assistantMessage]);
      setIsTyping(false);
    }, 2000);
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const SidebarContent = () => (
    <div className="flex flex-col h-full">
      {/* User Profile */}
      <div className="p-6 border-b border-border/50">
        <div className="flex items-center gap-3">
          <Avatar className="h-11 w-11 ring-2 ring-primary/30 ring-offset-2 ring-offset-background">
            <AvatarFallback className="bg-gradient-to-br from-primary to-accent text-background font-bold text-lg" style={{ fontFamily: 'var(--font-display)' }}>
              {userName[0]}
            </AvatarFallback>
          </Avatar>
          <div>
            <div className="font-semibold text-foreground" style={{ fontFamily: 'var(--font-display)' }}>{userName}</div>
            <div className="text-xs text-muted-foreground" style={{ fontFamily: 'var(--font-mono)' }}>Hesabım</div>
          </div>
        </div>
      </div>

      {/* New Chat Button */}
      <div className="p-4">
        <Button 
          className="w-full bg-gradient-to-r from-primary to-accent hover:shadow-lg hover:shadow-primary/25 transition-all duration-300 font-semibold"
          style={{ fontFamily: 'var(--font-display)' }}
        >
          <Plus className="w-4 h-4 mr-2" />
          Yeni Sohbet
        </Button>
      </div>

      {/* Previous Conversations */}
      <ScrollArea className="flex-1 px-4">
        <div className="space-y-1">
          <div className="text-xs font-bold uppercase tracking-wider text-muted-foreground mb-3 px-2" style={{ fontFamily: 'var(--font-display)' }}>
            Önceki Sohbetler
          </div>
          {conversations.map((conv, idx) => (
            <button
              key={conv.id}
              className="conversation-item w-full text-left p-3 rounded-lg hover:bg-card transition-colors duration-200 group"
              style={{ animationDelay: `${idx * 50}ms` }}
            >
              <div className="font-medium text-sm text-foreground group-hover:text-primary transition-colors" style={{ fontFamily: 'var(--font-display)' }}>
                {conv.title}
              </div>
              <div className="text-xs text-muted-foreground mt-1 line-clamp-1">
                {conv.preview}
              </div>
              <div className="text-xs text-muted-foreground/60 mt-1" style={{ fontFamily: 'var(--font-mono)' }}>
                {formatTimestamp(conv.timestamp)}
              </div>
            </button>
          ))}
        </div>
      </ScrollArea>
    </div>
  );

  return (
    <div className="flex h-[100dvh] bg-background relative z-10">
      {/* Desktop Sidebar */}
      <aside className="hidden md:flex w-80 border-r border-border/50 flex-col bg-card/30 backdrop-blur-sm">
        <SidebarContent />
      </aside>

      {/* Main Chat Area */}
      <main className="flex-1 flex flex-col relative">
        {/* Header with gradient accent */}
        <header className="border-b border-border/50 bg-card/30 backdrop-blur-sm relative overflow-hidden">
          <div className="absolute top-0 left-0 right-0 h-1 bg-gradient-to-r from-primary via-accent to-primary bg-[length:200%_100%] animate-[gradient-shift_3s_ease-in-out_infinite]"></div>
          
          <div className="p-4 flex items-center justify-between">
            <div className="flex items-center gap-3">
              {/* Mobile Menu */}
              <Sheet>
                <SheetTrigger asChild>
                  <Button variant="ghost" size="icon" className="md:hidden">
                    <Menu className="w-5 h-5" />
                  </Button>
                </SheetTrigger>
                <SheetContent side="left" className="p-0 w-80">
                  <SidebarContent />
                </SheetContent>
              </Sheet>

              <div>
                <h1 className="text-xl font-bold gradient-text" style={{ fontFamily: 'var(--font-display)' }}>
                  Nico
                </h1>
                <p className="text-xs text-muted-foreground" style={{ fontFamily: 'var(--font-mono)' }}>
                  Kişisel AI Asistanın
                </p>
              </div>
            </div>

            <div className="flex items-center gap-2">
              <div className="h-2 w-2 rounded-full bg-primary animate-pulse"></div>
              <span className="text-xs text-muted-foreground" style={{ fontFamily: 'var(--font-mono)' }}>Aktif</span>
            </div>
          </div>
        </header>

        {/* Messages */}
        <ScrollArea className="flex-1 p-4 md:p-6" ref={scrollRef}>
          <div className="max-w-3xl mx-auto space-y-4">
            {messages.map((message, idx) => (
              <div
                key={message.id}
                className={`message-bubble flex gap-3 ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
                style={{ animationDelay: `${idx * 50}ms` }}
              >
                {message.role === 'assistant' && (
                  <Avatar className="h-8 w-8 ring-2 ring-primary/20 flex-shrink-0">
                    <AvatarFallback className="bg-gradient-to-br from-primary to-accent text-background text-xs font-bold">
                      N
                    </AvatarFallback>
                  </Avatar>
                )}
                
                <div className={`flex flex-col ${message.role === 'user' ? 'items-end' : 'items-start'} max-w-[85%] md:max-w-[70%]`}>
                  <div
                    className={`rounded-2xl px-4 py-3 ${
                      message.role === 'user'
                        ? 'bg-gradient-to-br from-primary to-accent text-background shadow-lg shadow-primary/20'
                        : 'bg-card border border-border/50'
                    }`}
                  >
                    <p className="text-sm leading-relaxed whitespace-pre-wrap">
                      {message.content}
                    </p>
                  </div>
                  <span className="text-xs text-muted-foreground mt-1 px-1" style={{ fontFamily: 'var(--font-mono)' }}>
                    {formatTimestamp(message.timestamp)}
                  </span>
                </div>

                {message.role === 'user' && (
                  <Avatar className="h-8 w-8 ring-2 ring-primary/20 flex-shrink-0">
                    <AvatarFallback className="bg-secondary text-foreground text-xs font-semibold">
                      {userName[0]}
                    </AvatarFallback>
                  </Avatar>
                )}
              </div>
            ))}

            {/* Typing Indicator */}
            {isTyping && (
              <div className="flex gap-3 justify-start animate-bounce-in">
                <Avatar className="h-8 w-8 ring-2 ring-primary/20">
                  <AvatarFallback className="bg-gradient-to-br from-primary to-accent text-background text-xs font-bold">
                    N
                  </AvatarFallback>
                </Avatar>
                <div className="bg-card border border-border/50 rounded-2xl px-4 py-3 flex items-center gap-1">
                  <div className="typing-dot h-2 w-2 rounded-full bg-primary"></div>
                  <div className="typing-dot h-2 w-2 rounded-full bg-primary"></div>
                  <div className="typing-dot h-2 w-2 rounded-full bg-primary"></div>
                </div>
              </div>
            )}
          </div>
        </ScrollArea>

        {/* Input Area */}
        <div className="border-t border-border/50 bg-card/30 backdrop-blur-sm p-4">
          <div className="max-w-3xl mx-auto">
            <div className="flex gap-2">
              <Input
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyPress={handleKeyPress}
                placeholder="Mesajını yaz..."
                className="flex-1 bg-background/50 border-border/50 focus-visible:ring-primary focus-visible:ring-offset-0 focus-visible:border-primary transition-all"
              />
              <Button
                onClick={handleSend}
                disabled={!input.trim()}
                className="bg-gradient-to-r from-primary to-accent hover:shadow-lg hover:shadow-primary/25 hover:scale-105 transition-all duration-300 disabled:opacity-50 disabled:hover:scale-100"
                size="icon"
              >
                <Send className="w-4 h-4" />
              </Button>
            </div>
            <p className="text-xs text-muted-foreground/60 text-center mt-2" style={{ fontFamily: 'var(--font-mono)' }}>
              Nico her zaman yardıma hazır • Türkçe ve samimi 💙
            </p>
          </div>
        </div>
      </main>
    </div>
  );
}

export default App;
