'use client'

import { useState, useEffect, useRef } from 'react'
import { Button } from "@/components/ui/button"
import { Textarea } from "@/components/ui/textarea"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Slider } from "@/components/ui/slider"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Label } from "@/components/ui/label"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Input } from "@/components/ui/input"
import { Settings2, Sparkles, AudioWaveform, Loader2, Mic, Upload, Trash2, Play, Pause } from "lucide-react"
import { gsap } from "gsap"
import { useGSAP } from "@gsap/react"
import { toast } from "sonner"
import { Voice, Emotion } from "@/lib/types"
import { api } from "@/lib/api"

export default function Home() {
  const [text, setText] = useState('')
  const [loading, setLoading] = useState(false)
  const [audioUrl, setAudioUrl] = useState('')
  const [error, setError] = useState('')

  // Data
  const [voices, setVoices] = useState<Voice[]>([])
  const [emotions, setEmotions] = useState<Record<string, any>>({})

  // Settings
  const [selectedVoice, setSelectedVoice] = useState<string>('')
  const [selectedEmotion, setSelectedEmotion] = useState<string>('neutral')
  const [speed, setSpeed] = useState([1.0])
  const [pitch, setPitch] = useState([1.0])
  const [energy, setEnergy] = useState([1.0])
  const [showSettings, setShowSettings] = useState(false)

  // Update sliders when emotion changes
  useEffect(() => {
    if (selectedEmotion && emotions[selectedEmotion]) {
      const defaults = emotions[selectedEmotion]
      setSpeed([defaults.speed])
      setPitch([defaults.pitch])
      setEnergy([defaults.energy])
    }
  }, [selectedEmotion, emotions])

  // Voice Cloning State
  const [cloneName, setCloneName] = useState('')
  const [cloneFile, setCloneFile] = useState<File | null>(null)
  const [isCloning, setIsCloning] = useState(false)
  const [playingVoice, setPlayingVoice] = useState<string | null>(null)

  const audioRef = useRef<HTMLAudioElement>(null)

  // Refs for animations
  const containerRef = useRef<HTMLDivElement>(null)
  const settingsPanelRef = useRef<HTMLDivElement>(null)
  const mainPanelRef = useRef<HTMLDivElement>(null)
  const advancedControlsRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    // Fetch initial data
    const fetchData = async () => {
      try {
        const [voicesRes, emotionsRes] = await Promise.all([
          api.voices.list(),
          api.emotions.list()
        ])

        if (voicesRes.success) setVoices(voicesRes.voices)
        if (emotionsRes.success) setEmotions(emotionsRes.emotions)
      } catch (err) {
        console.error('Failed to load initial data:', err)
      }
    }
    fetchData()
  }, [])

  useGSAP(() => {
    const tl = gsap.timeline()

    tl.from([settingsPanelRef.current, mainPanelRef.current], {
      y: 50,
      opacity: 0,
      duration: 0.8,
      stagger: 0.2,
      ease: "power3.out"
    })

  }, { scope: containerRef })

  // Animate advanced controls
  useGSAP(() => {
    if (showSettings) {
      gsap.fromTo(advancedControlsRef.current,
        { height: 0, opacity: 0 },
        { height: "auto", opacity: 1, duration: 0.4, ease: "power2.out" }
      )
    }
  }, [showSettings])

  const handleClone = async () => {
    if (!cloneName || !cloneFile) {
      toast.error("Missing information", { description: "Please provide a name and an audio file." })
      return
    }

    setIsCloning(true)
    try {
      if (!cloneFile) throw new Error("Audio file missing")

      const formData = new FormData()
      formData.append('voice_name', cloneName)
      formData.append('audio_file', cloneFile)
      formData.append('description', 'Cloned via Web UI')

      const data = await api.voices.create(formData)

      if (data.success) {
        toast.success("Voice Cloned Successfully!", { description: `${cloneName} is now available.` })
        setCloneName('')
        setCloneFile(null)
        // Refresh voices
        const voicesRes = await api.voices.list()
        if (voicesRes.success) setVoices(voicesRes.voices)
      } else {
        throw new Error(data.detail)
      }
    } catch (err: any) {
      toast.error("Cloning Failed", { description: err.message || "Unknown error occurred." })
    } finally {
      setIsCloning(false)
    }
  }

  const handleDeleteVoice = async (id: string, e: React.MouseEvent) => {
    e.stopPropagation()
    if (!confirm("Are you sure you want to delete this voice?")) return

    try {
      const data = await api.voices.delete(id)
      if (data.success) {
        toast.success("Voice Deleted")
        setVoices(voices.filter(v => v.id !== id))
        if (selectedVoice === id) setSelectedVoice('')
      }
    } catch (err) {
      toast.error("Delete Failed")
    }
  }

  const handleGenerate = async () => {
    if (!text.trim()) return

    setLoading(true)
    setError('')
    setAudioUrl('')

    try {
      const formData = new FormData()
      formData.append('text', text)
      // Use emotional engine by default for best quality
      formData.append('engine', 'emotional')
      formData.append('language', 'en')
      formData.append('emotion', selectedEmotion)
      formData.append('speed', speed[0].toString())
      formData.append('pitch', pitch[0].toString())
      formData.append('energy', energy[0].toString())

      if (selectedVoice) {
        formData.append('voice_id', selectedVoice)
      }

      const data = await api.tts.synthesize(formData)

      if (data.success && data.audio_url) {
        setAudioUrl(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}${data.audio_url}`)
        toast.success("Speech generated successfully!", {
          description: "playing audio...",
        })
        // Auto play
        setTimeout(() => {
          if (audioRef.current) {
            audioRef.current.play().catch(e => console.log("Auto-play prevented:", e))
            audioRef.current.onended = () => setPlayingVoice(null)
          }
        }, 100)
      } else {
        toast.error("Failed to generate speech", {
          description: data.detail || "Please try again.",
        })
      }
    } catch (err) {
      toast.error("Connection Failed", {
        description: "Could not connect to the synthesis engine. Is the backend running?",
      })
    } finally {
      setLoading(false)
    }
  }

  return (
    <div ref={containerRef} className="min-h-screen bg-background text-foreground bg-[radial-gradient(ellipse_at_top,_var(--tw-gradient-stops))] from-indigo-100/20 via-background to-background dark:from-slate-900 dark:via-background dark:to-background overflow-hidden selection:bg-primary/20">
      <main className="max-w-7xl mx-auto p-6 pt-8">

        <Tabs defaultValue="tts" className="w-full space-y-6">
          <div className="flex items-center justify-between">
            <TabsList className="bg-secondary/50 p-1 border border-white/5 h-auto flex-wrap justify-start">
              <TabsTrigger value="tts" className="px-6 data-[state=active]:bg-background/80 data-[state=active]:shadow-lg flex-1 sm:flex-none">
                Text to Speech
              </TabsTrigger>
              <TabsTrigger value="voice-lab" className="px-6 data-[state=active]:bg-background/80 data-[state=active]:shadow-lg flex-1 sm:flex-none">
                Voice Lab <span className="ml-2 px-1.5 py-0.5 rounded-full bg-indigo-500/20 text-indigo-300 text-[10px] font-bold">NEW</span>
              </TabsTrigger>
            </TabsList>
          </div>

          {/* TAB 1: TEXT TO SPEECH */}
          <TabsContent value="tts" className="space-y-6 m-0 focus-visible:outline-none data-[state=active]:animate-in data-[state=active]:fade-in data-[state=active]:slide-in-from-bottom-2 duration-500">
            <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
              {/* Left Panel: Settings */}
              <div ref={settingsPanelRef} className="lg:col-span-4 space-y-6">
                <Card className="border-border/40 bg-card/40 backdrop-blur-xl shadow-xl">
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2 text-lg font-medium">
                      <Settings2 className="w-4 h-4 text-primary" />
                      Configuration
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-6">

                    {/* Voice Selection */}
                    <div className="space-y-3">
                      <Label>Voice Model</Label>
                      <Select value={selectedVoice} onValueChange={setSelectedVoice}>
                        <SelectTrigger className="bg-secondary/30 border-white/10">
                          <SelectValue placeholder="Select a voice" />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="default">Default Voice (Nova)</SelectItem>
                          {voices.map((v) => (
                            <SelectItem key={v.id} value={v.id}>
                              {v.name} {v.description && <span className="text-muted-foreground ml-2 text-xs">({v.description})</span>}
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </div>

                    {/* Emotion Selection */}
                    <div className="space-y-3">
                      <Label>Emotion & Style</Label>
                      <Select value={selectedEmotion} onValueChange={setSelectedEmotion}>
                        <SelectTrigger className="bg-secondary/30 border-white/10">
                          <SelectValue placeholder="Select emotion" />
                        </SelectTrigger>
                        <SelectContent>
                          {Object.keys(emotions).map((e) => (
                            <SelectItem key={e} value={e}>
                              {e.charAt(0).toUpperCase() + e.slice(1)}
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </div>

                    {/* Advanced Controls Toggle */}
                    <div className="pt-4 border-t border-border/40">
                      <Button
                        variant="ghost"
                        size="sm"
                        className="w-full justify-between hover:bg-secondary/50"
                        onClick={() => setShowSettings(!showSettings)}
                      >
                        Advanced Controls
                        <Settings2 className="w-4 h-4 ml-2 opacity-50 transition-transform duration-300" style={{ transform: showSettings ? 'rotate(180deg)' : 'rotate(0deg)' }} />
                      </Button>

                      {showSettings && (
                        <div ref={advancedControlsRef} className="overflow-hidden">
                          <div className="space-y-6 mt-6 p-1">
                            <div className="space-y-3">
                              <div className="flex justify-between">
                                <Label className="text-xs font-normal text-muted-foreground">Speed</Label>
                                <span className="text-xs font-mono text-primary">{speed[0]}x</span>
                              </div>
                              <Slider
                                value={speed}
                                onValueChange={setSpeed}
                                min={0.5}
                                max={2.0}
                                step={0.1}
                                className="py-2"
                              />
                            </div>
                            <div className="space-y-3">
                              <div className="flex justify-between">
                                <Label className="text-xs font-normal text-muted-foreground">Pitch</Label>
                                <span className="text-xs font-mono text-primary">{pitch[0]}</span>
                              </div>
                              <Slider
                                value={pitch}
                                onValueChange={setPitch}
                                min={0.5}
                                max={1.5}
                                step={0.1}
                                className="py-2"
                              />
                            </div>
                            <div className="space-y-3">
                              <div className="flex justify-between">
                                <Label className="text-xs font-normal text-muted-foreground">Energy</Label>
                                <span className="text-xs font-mono text-primary">{energy[0]}</span>
                              </div>
                              <Slider
                                value={energy}
                                onValueChange={setEnergy}
                                min={0.5}
                                max={2.0}
                                step={0.1}
                                className="py-2"
                              />
                            </div>
                          </div>
                        </div>
                      )}
                    </div>

                  </CardContent>
                </Card>
              </div>

              {/* Right Panel: Input & Output */}
              <div ref={mainPanelRef} className="lg:col-span-8 space-y-6">
                <Card className="border-border/40 bg-card/40 backdrop-blur-xl min-h-[550px] flex flex-col relative overflow-hidden ring-1 ring-white/10 shadow-2xl group">
                  <div className="absolute top-0 left-0 w-full h-0.5 bg-gradient-to-r from-indigo-500 via-purple-500 to-pink-500 opacity-70" />

                  <CardContent className="p-0 flex-1 flex flex-col relative">
                    <Textarea
                      value={text}
                      onChange={(e) => setText(e.target.value)}
                      placeholder="Start typing or paste text to generate lifelike speech..."
                      className="flex-1 resize-none border-0 focus-visible:ring-0 bg-transparent p-8 text-xl leading-relaxed font-light placeholder:text-muted-foreground/30 selection:bg-indigo-500/30 text-foreground"
                      spellCheck={false}
                    />

                    <div className="absolute bottom-4 right-4 text-xs text-muted-foreground bg-background/50 px-2 py-1 rounded backdrop-blur-md border border-white/5">
                      {text.trim().length} chars
                    </div>
                  </CardContent>

                  <div className="p-6 bg-secondary/10 border-t border-white/5 space-y-4 backdrop-blur-sm">
                    {/* Audio Player and Status */}
                    <div className="min-h-[60px] flex items-center justify-center">
                      {audioUrl ? (
                        <div className="flex items-center gap-4 w-full bg-white/5 p-3 rounded-xl border border-white/5 animate-in fade-in slide-in-from-bottom-2">
                          <div className="h-10 w-10 rounded-full bg-indigo-500 flex items-center justify-center flex-shrink-0 animate-pulse">
                            <Play className="w-5 h-5 text-white fill-current" />
                          </div>
                          <audio ref={audioRef} controls src={audioUrl} className="w-full h-8 opacity-80" />
                        </div>
                      ) : (
                        <div className="text-sm text-muted-foreground/50 italic flex items-center gap-2">
                          <Sparkles className="w-3 h-3" />
                          Ready to generate
                        </div>
                      )}
                    </div>

                    <div className="flex justify-end pt-2">
                      <Button
                        size="lg"
                        onClick={handleGenerate}
                        disabled={loading || !text.trim()}
                        className="text-primary-foreground font-semibold shadow-[0_0_30px_-5px_rgba(255,255,255,0.3)] transition-all hover:scale-[1.02] hover:shadow-indigo-500/20 rounded-full px-8 h-12"
                      >
                        {loading ? (
                          <>
                            <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                            Synthesizing...
                          </>
                        ) : (
                          <>
                            Generate Speech
                            <Sparkles className="w-4 h-4 ml-2" />
                          </>
                        )}
                      </Button>
                    </div>
                  </div>
                </Card>
              </div>
            </div>
          </TabsContent>

          {/* TAB 2: VOICE LAB */}
          <TabsContent value="voice-lab" className="data-[state=active]:animate-in data-[state=active]:fade-in duration-500 focus-visible:outline-none">
            <div className="grid grid-cols-1 md:grid-cols-12 gap-8">

              {/* Clone New Voice */}
              <Card className="md:col-span-5 h-fit border-border/40 bg-card/40 backdrop-blur-xl">
                <CardHeader>
                  <CardTitle className="text-lg flex items-center gap-2">
                    <Mic className="w-4 h-4 text-primary" />
                    Clone New Voice
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-6">
                  <div className="p-4 rounded-lg bg-indigo-500/10 border border-indigo-500/20 text-indigo-200 text-sm mb-4">
                    Instant Voice Cloning requires only a 30s sample.
                  </div>

                  <div className="space-y-3">
                    <Label>Voice Name</Label>
                    <Input
                      placeholder="e.g. My Narrator Voice"
                      value={cloneName}
                      onChange={(e) => setCloneName(e.target.value)}
                      className="bg-secondary/30 border-white/10"
                    />
                  </div>

                  <div className="space-y-3">
                    <Label>Audio Sample</Label>
                    <div className="border-2 border-dashed border-white/10 rounded-xl p-8 transition-colors hover:border-primary/50 hover:bg-primary/5 group relative cursor-pointer">
                      <input
                        type="file"
                        accept="audio/*"
                        onChange={(e) => setCloneFile(e.target.files?.[0] || null)}
                        className="absolute inset-0 w-full h-full opacity-0 cursor-pointer z-10"
                      />
                      <div className="flex flex-col items-center justify-center text-center gap-3">
                        <div className="h-10 w-10 rounded-full bg-secondary flex items-center justify-center group-hover:scale-110 transition-transform">
                          <Upload className="w-5 h-5 text-muted-foreground group-hover:text-primary transition-colors" />
                        </div>
                        <div className="space-y-1">
                          <p className="font-medium text-sm text-foreground">
                            {cloneFile ? cloneFile.name : "Click to upload audio"}
                          </p>
                          <p className="text-xs text-muted-foreground">
                            {cloneFile ? `${(cloneFile.size / 1024 / 1024).toFixed(2)} MB` : "WAV, MP3 up to 10MB"}
                          </p>
                        </div>
                      </div>
                    </div>
                  </div>

                  <Button
                    className="w-full h-11 mt-4"
                    disabled={isCloning || !cloneName || !cloneFile}
                    onClick={handleClone}
                  >
                    {isCloning ? (
                      <>
                        <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                        Cloning Voice...
                      </>
                    ) : (
                      "Clone Voice"
                    )}
                  </Button>
                </CardContent>
              </Card>

              {/* Your Voices List */}
              <Card className="md:col-span-7 border-border/40 bg-card/40 backdrop-blur-xl min-h-[500px]">
                <CardHeader className="border-b border-white/5 pb-4">
                  <CardTitle className="text-lg flex items-center justify-between">
                    <span>Your Voice Library</span>
                    <span className="text-xs px-2 py-1 rounded bg-secondary font-mono text-muted-foreground">{voices.length} Voices</span>
                  </CardTitle>
                </CardHeader>
                <CardContent className="p-0">
                  {voices.length === 0 ? (
                    <div className="flex flex-col items-center justify-center h-[300px] text-muted-foreground p-8 text-center">
                      <Mic className="w-12 h-12 mb-4 opacity-20" />
                      <p>No voices cloned yet.</p>
                      <p className="text-sm opacity-50">Upload a sample to get started.</p>
                    </div>
                  ) : (
                    <div className="divide-y divide-white/5">
                      {voices.map((voice) => (
                        <div key={voice.id} className="flex items-center justify-between p-4 hover:bg-secondary/20 transition-colors group">
                          <div className="flex items-center gap-4">
                            <div className="h-10 w-10 rounded-full bg-gradient-to-br from-indigo-500/20 to-purple-500/20 text-indigo-400 flex items-center justify-center text-sm font-bold border border-white/10">
                              {voice.name.charAt(0).toUpperCase()}
                            </div>
                            <div>
                              <h4 className="font-medium">{voice.name}</h4>
                              <p className="text-xs text-muted-foreground">{voice.description || "Cloned Voice"}</p>
                            </div>
                          </div>
                          <div className="flex items-center gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
                            <Button
                              variant="ghost"
                              size="icon"
                              className="h-8 w-8 hover:text-red-400 hover:bg-red-400/10"
                              onClick={(e) => handleDeleteVoice(voice.id, e)}
                            >
                              <Trash2 className="w-4 h-4" />
                            </Button>
                            <Button
                              size="sm"
                              variant="secondary"
                              onClick={() => {
                                setSelectedVoice(voice.id);
                                const ttsTab = document.querySelector('[value="tts"]') as HTMLElement;
                                ttsTab?.click();
                                toast.info(`Selected ${voice.name}`, { description: "Ready to generate speech." });
                              }}
                            >
                              Use
                            </Button>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </CardContent>
              </Card>
            </div>
          </TabsContent>
        </Tabs>
      </main>
    </div>
  )
}
