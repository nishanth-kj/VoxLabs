import { Button } from "@/components/ui/button"
import { Code2, ArrowRight, Terminal } from "lucide-react"
import Link from "next/link"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"

export function ApiSection(props: React.HTMLAttributes<HTMLElement>) {
    return (
        <section id="api" className="py-24 px-6 bg-secondary/20 border-t border-border/40" {...props}>
            <div className="max-w-5xl mx-auto space-y-12">

                {/* Header */}
                <div className="text-center space-y-6">
                    <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-emerald-500/10 mb-4 border border-emerald-500/20">
                        <Code2 className="w-8 h-8 text-emerald-500" />
                    </div>
                    <h2 className="text-3xl md:text-5xl font-bold tracking-tight">
                        Developer API
                    </h2>
                    <p className="text-xl text-muted-foreground max-w-2xl mx-auto">
                        Integrate VoxLabs' state-of-the-art voice synthesis directly into your applications.
                    </p>
                    <div className="flex justify-center gap-4">
                        <Link href="/docs">
                            <Button size="lg" className="h-12 px-8 shadow-lg shadow-emerald-500/20">
                                Read the Docs
                                <ArrowRight className="ml-2 w-4 h-4" />
                            </Button>
                        </Link>
                    </div>
                </div>

                {/* Code Example Section */}
                <div className="bg-card/50 border border-border/40 rounded-xl overflow-hidden shadow-2xl">
                    <div className="bg-muted/50 px-4 py-3 border-b border-border/40 flex items-center gap-2">
                        <Terminal className="w-4 h-4 text-muted-foreground" />
                        <span className="text-sm font-mono text-muted-foreground">Quickstart</span>
                    </div>
                    <div className="p-6">
                        <Tabs defaultValue="python" className="w-full">
                            <TabsList className="mb-4">
                                <TabsTrigger value="python">Python</TabsTrigger>
                                <TabsTrigger value="javascript">JavaScript</TabsTrigger>
                                <TabsTrigger value="curl">cURL</TabsTrigger>
                            </TabsList>

                            <TabsContent value="python" className="mt-0">
                                <pre className="bg-slate-950 p-6 rounded-lg overflow-x-auto text-sm font-mono text-blue-100 leading-relaxed">
                                    {`import requests

url = "http://localhost:8000/api/tts"
payload = {
    "text": "Hello world! This is a test of the VoxLabs API.",
    "emotion": "happy",
    "speed": 1.1
}

response = requests.post(url, data=payload)

with open("output.mp3", "wb") as f:
    f.write(response.content)

print("Audio saved as output.mp3")`}
                                </pre>
                            </TabsContent>

                            <TabsContent value="javascript" className="mt-0">
                                <pre className="bg-slate-950 p-6 rounded-lg overflow-x-auto text-sm font-mono text-yellow-100 leading-relaxed">
                                    {`const formData = new FormData();
formData.append('text', 'Hello world! This is a test.');
formData.append('emotion', 'excited');

fetch('http://localhost:8000/api/tts', {
    method: 'POST',
    body: formData
})
.then(response => response.blob())
.then(blob => {
    const url = window.URL.createObjectURL(blob);
    const audio = new Audio(url);
    audio.play();
});`}
                                </pre>
                            </TabsContent>

                            <TabsContent value="curl" className="mt-0">
                                <pre className="bg-slate-950 p-6 rounded-lg overflow-x-auto text-sm font-mono text-green-100 leading-relaxed">
                                    {`curl -X POST http://localhost:8000/api/tts \\
     -F "text=Hello world!" \\
     -F "emotion=confident" \\
     -o output.mp3`}
                                </pre>
                            </TabsContent>
                        </Tabs>
                    </div>
                </div>
            </div>
        </section>
    )
}
