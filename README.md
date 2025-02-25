This is tool to customise cover letters based on a CV and a job description.
It uses a locally hosted ollama instance to generate the cover letter.

![image](https://github.com/user-attachments/assets/b633a897-cd03-465e-95ec-991000f31aa9)


Note: /api/generate is an ollama endpoint, not openwebui, so only native ollama models are available with ollama native settings. openwebui magics higher contexts onto gpu, but ollama is by default is more conservative. something like 4k is possible with deepseek-r1:32b, and maybe about 30k with phi4:14b
