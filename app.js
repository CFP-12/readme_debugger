let pyodide = null;

// 페이지 로드 시 엔진 및 패키지 구조 초기화
async function initEngine() {
    const statusDiv = document.getElementById('status');
    try {
        pyodide = await loadPyodide();
        await pyodide.loadPackage("micropip"); 
        
        statusDiv.innerText = "⚡ 엔진 구동 완료! 실제 패키지 구조 가상 조립 중...";

        await pyodide.runPythonAsync(
`import os
os.makedirs('/home/pyodide/src', exist_ok=True)
os.makedirs('/home/pyodide/src/pydoccheck', exist_ok=True)
os.makedirs('/home/pyodide/src/pydoccheck/models', exist_ok=True)
os.makedirs('/home/pyodide/src/pydoccheck/utils', exist_ok=True)
os.makedirs('/home/pyodide/src/pydoccheck/reporting', exist_ok=True)
os.makedirs('/home/pyodide/src/pydoccheck/parsers', exist_ok=True)

with open('/home/pyodide/src/__init__.py', 'w') as f: pass
with open('/home/pyodide/src/pydoccheck/__init__.py', 'w') as f: pass
with open('/home/pyodide/src/pydoccheck/models/__init__.py', 'w') as f: pass
with open('/home/pyodide/src/pydoccheck/utils/__init__.py', 'w') as f: pass
with open('/home/pyodide/src/pydoccheck/reporting/__init__.py', 'w') as f: pass

parsers_init_code = """from .markdown_parser import MarkdownParser
from .rst_parser import RSTParser"""

with open('/home/pyodide/src/pydoccheck/parsers/__init__.py', 'w') as f:
    f.write(parsers_init_code.strip())`
        );

        const modules = [
            { url: 'src/pydoccheck/models/code_block.py', path: '/home/pyodide/src/pydoccheck/models/code_block.py' },
            { url: 'src/pydoccheck/utils/helpers.py', path: '/home/pyodide/src/pydoccheck/utils/helpers.py' },
            { url: 'src/pydoccheck/reporting/analyzer.py', path: '/home/pyodide/src/pydoccheck/reporting/analyzer.py' },
            { url: 'src/pydoccheck/parsers/markdown_parser.py', path: '/home/pyodide/src/pydoccheck/parsers/markdown_parser.py' },
            { url: 'src/pydoccheck/parsers/rst_parser.py', path: '/home/pyodide/src/pydoccheck/parsers/rst_parser.py' }
        ];

        for (const mod of modules) {
            try {
                const res = await fetch(mod.url);
                if (!res.ok) {
                    console.error(`🟥 [파일 유실] 웹 서버 경로에 파일이 없습니다 (404): ${mod.url}`);
                    continue;
                }
                const code = await res.text();
                pyodide.FS.writeFile(mod.path, code);
            } catch (fileErr) {
                console.error(`⚠️ 모듈 주입 오류 (${mod.url}):`, fileErr.message);
            }
        }

        statusDiv.innerHTML = "✅ <b>시스템 가동 완료!</b>";
        document.getElementById('gitBtn').disabled = false;
        document.getElementById('zipBtn').disabled = false;

    } catch (err) {
        statusDiv.innerHTML = "❌ 엔진 초기화 오류 발생: " + err.message;
    }
}

// GitHub 주소 분석 및 브랜치 자동 인식 구조
document.getElementById('gitBtn').addEventListener('click', async () => {
    let repoUrl = document.getElementById('repoUrl').value.trim();
    const output = document.getElementById('output');
    if(!repoUrl) return alert("GitHub 주소를 입력해주세요!");

    output.innerText = "🔄 GitHub 레포지토리 및 브랜치 구조 분석 중...";

    try {
        repoUrl = repoUrl.replace(/\.git$/, "").replace(/\/$/, "");

        let owner = "";
        let repo = "";
        let branch = "main"; 

        const gitRegex = /https:\/\/github\.com\/([^\/]+)\/([^\/]+)(?:\/tree\/([^\s]+))?/;
        const match = repoUrl.match(gitRegex);

        if (match) {
            owner = match[1];
            repo = match[2];
            if (match[3]) {
                branch = match[3]; 
            }
        } else {
            throw new Error("올바른 GitHub 저장소 형식이 아닙니다.");
        }

        output.innerText = `🟩 [${branch}] 브랜치 감지 완료! 프로젝트 메타데이터 조회 중...`;

        const treeRes = await fetch(`https://api.github.com/repos/${owner}/${repo}/git/trees/${branch}?recursive=1`);
        if(!treeRes.ok) {
            if(branch === "main") {
                const tryMasterRes = await fetch(`https://api.github.com/repos/${owner}/${repo}/git/trees/master?recursive=1`);
                if(tryMasterRes.ok) {
                    branch = "master";
                    const treeData = await tryMasterRes.json();
                    return processTreeAndRun(treeData.tree, owner, repo, branch);
                }
            }
            throw new Error(`[${branch}] 브랜치 정보를 가져올 수 없습니다. 브랜치명이 정확한지 확인해 주세요.`);
        }
        
        const treeData = await treeRes.json();
        await processTreeAndRun(treeData.tree, owner, repo, branch);

    } catch(err) {
        output.innerHTML = `<div class="error-box">🚨 GitHub 연동 실패: ${err.message}</div>`;
    }
});

async function processTreeAndRun(treeList, owner, repo, branch) {
    const output = document.getElementById('output');
    const files = treeList.map(f => f.path);

    const isPythonProject = files.some(f => f.endsWith('.py') || f === 'requirements.txt' || f === 'setup.py');
    
    if (!isPythonProject) {
        output.innerHTML = `<div class="error-box">❌ <b>분석 거부:</b> 해당 저장소는 Python 기반 프로젝트가 아닙니다.</div>`;
        return;
    }

    output.innerText = `🟩 Python 프로젝트 확인! [${branch}] 브랜치의 README.md 다운로드 중...`;
    const readmeRes = await fetch(`https://raw.githubusercontent.com/${owner}/${repo}/${branch}/README.md`);
    if(!readmeRes.ok) throw new Error(`[${branch}] 브랜치 최상위 경로에서 README.md 파일을 찾을 수 없습니다.`);
    
    const readmeContent = await readmeRes.text();
    
    runValidation(readmeContent, `${owner}/${repo} (${branch})`);
}

// 기능 2: 로컬 ZIP 파일 업로드 및 브라우저 내 해제 구조
document.getElementById('zipBtn').addEventListener('click', async () => {
    const fileInput = document.getElementById('zipFile');
    const output = document.getElementById('output');
    if(fileInput.files.length === 0) return alert("분석할 .zip 파일을 선택해 주세요!");

    output.innerText = "🔄 브라우저 샌드박스 내부에서 ZIP 압축 해제 중...";
    const file = fileInput.files[0];

    try {
        const jszip = new JSZip();
        const zip = await jszip.loadAsync(file);
        
        let readmeContent = "";
        
        for (let relativePath in zip.files) {
            if (relativePath.toLowerCase().endsWith("readme.md")) {
                readmeContent = await zip.files[relativePath].async("text");
                break;
            }
        }

        if(!readmeContent) {
            output.innerHTML = `<div class="error-box">❌ <b>분석 실패:</b> 업로드된 ZIP 파일 내부에 README.md 파일이 존재하지 않습니다.</div>`;
            return;
        }

        runValidation(readmeContent, file.name);

    } catch(err) {
        output.innerHTML = `<div class="error-box">🚨 ZIP 처리 오류: ${err.message}</div>`;
    }
});

// 핵심 공통 샌드박스 검증 및 추천 가이드 출력 엔진
async function runValidation(mdContent, sourceName) {
    const output = document.getElementById('output');
    
    try {
        pyodide.FS.writeFile('/home/pyodide/temp_target.md', mdContent);

        const jsonResult = await pyodide.runPythonAsync(`
            import sys
            import json
            if '/home/pyodide' not in sys.path:
                sys.path.insert(0, '/home/pyodide')

            from src.pydoccheck.utils.helpers import parse_document
            
            blocks = parse_document('/home/pyodide/temp_target.md')
            
            results = []
            for b in blocks:
                if b.is_executable and b.language.lower() == 'python':
                    try:
                        exec(b.content, {})
                        results.append({"block_id": b.block_id, "code": b.content, "success": True, "error_type": "", "stderr": ""})
                    except Exception as e:
                        err_type = type(e).__name__
                        results.append({"block_id": b.block_id, "code": b.content, "success": False, "error_type": err_type, "stderr": str(e)})
            
            total = len(results)
            passed = sum(1 for r in results if r["success"])
            failed = total - passed
            pass_rate = round((passed / total) * 100, 1) if total > 0 else 0.0
            fail_rate = round(100 - pass_rate, 1) if total > 0 else 0.0

            json.dumps({
                "total": total, "passed": passed, "failed": failed, 
                "pass_rate": pass_rate, "fail_rate": fail_rate, "details": results
            })
        `);

        const data = JSON.parse(jsonResult);
        
        //  파이썬 예시 코드 블록이 0개일 때의 예외 처리 레이아웃 가동
        if (data.total === 0) {
            output.innerHTML = `
                <h2>📊 타깃 문서 분석: ${sourceName}</h2>
                <div style="background:#fff7ed; border:1px solid #ffedd5; color:#c2410c; padding:20px; border-radius:8px; border-left:5px solid #f97316;">
                    ⚠️ <b>분석 결과 알림:</b> 해당 문서(${sourceName}) 내부에서 
                    <code style="background:#ffedd5; padding:2px 4px;">python</code>으로 선언된 <b>실행 가능한 파이썬 코드 블록을 찾지 못했습니다.</b><br>
                    <span style="font-size:13px; color:#ea580c;">* 파이썬 프로젝트가 맞더라도 가이드 문서에 검증할 예시 코드가 없거나, 주석 처리된 일반 텍스트 블록일 수 있습니다.</span>
                </div>
            `;
            return;
        }

        // 코드 블록이 1개 이상 있을 때만 기존 대시보드를 정상 출력합.
        let htmlReport = `<h2>📊 [결과 요약] 타깃 문서: ${sourceName}</h2>`;
        htmlReport += `
            <table width="100%" style="border-collapse:collapse; margin-bottom:20px; font-size:15px;">
                <tr style="background:#e2e8f0; font-weight:bold;"><td style="padding:10px; border:1px solid #cbd5e1;">전체 검증 스니펫</td><td style="padding:10px; border:1px solid #cbd5e1;">실행 성공 (🟩)</td><td style="padding:10px; border:1px solid #cbd5e1;">실행 실패 (🟥)</td></tr>
                <tr><td style="padding:10px; border:1px solid #cbd5e1;">${data.total} 개</td><td style="padding:10px; border:1px solid #cbd5e1;"><span class="success-badge">${data.passed} 개 (${data.pass_rate}%)</span></td><td style="padding:10px; border:1px solid #cbd5e1;"><span class="fail-badge">${data.failed} 개 (${data.fail_rate}%)</span></td></tr>
            </table>
        `;

        // 코드 블록이 존재하면서 실패가 0개일 때만 완벽 통과 처리
        if(data.failed > 0) {
            htmlReport += `<h3>❌ 실패한 코드 블록 및 AI 정밀 추천 가이드</h3>`;
            data.details.forEach((res, index) => {
                if(!res.success) {
                    let recommendation = "정확한 내부 변수 바인딩 상태나 전처리 누락 여부를 점검하세요.";
                    if(res.error_type === "ModuleNotFoundError") {
                        recommendation = `💡 <b>[추천 수정]</b> 문서에 쓰인 모듈이 로컬 가상환경에 누락되었습니다. 터미널에 <code style="background:#fee2e2; padding:2px 4px;">pip install ${res.stderr.split("'")[1] || '해당모듈'}</code>을 실행하거나 requirements.txt에 선언을 보완하세요.`;
                    } else if(res.error_type === "NameError") {
                        recommendation = `💡 <b>[추천 수정]</b> 정의되지 않은 변수나 함수를 호출했습니다. 해당 스니펫 상단에 필수 변수 초기화 코드가 누락되었는지 확인하거나 오타를 교정하세요.`;
                    } else if(res.error_type === "SyntaxError") {
                        recommendation = `💡 <b>[추천 수정]</b> 괄호 미닫힘, 콜론(:) 누락 등 파이썬 기본 문법 위반입니다. 코드 블록의 들여쓰기와 타이포를 점검해 주세요.`;
                    } else if(res.error_type === "ZeroDivisionError") {
                        recommendation = `💡 <b>[추천 수정]</b> 값을 0으로 나누려고 시도했습니다. 분모 변수가 0이 되지 않도록 안전 제어 조건문(if)을 추가하는 편이 안전합니다.`;
                    }

                    htmlReport += `
                        <div style="background:#fff; border:1px solid #fca5a5; border-radius:6px; padding:15px; margin-bottom:15px; border-left:5px solid #ef4444;">
                            <div style="font-weight:bold; color:#b91c1c; margin-bottom:8px;">[실패 블록 #${index+1}] 에러 타입: ${res.error_type}</div>
                            <div style="font-weight:bold; color:#475569; font-size:13px;">📌 실패한 원본 소스코드 :</div>
                            <pre style="background:#1e293b; color:#f8fafc; padding:10px; border-radius:4px; overflow-x:auto;">${res.code}</pre>
                            <div style="color:#dc2626; font-size:13px; margin-bottom:10px;"><b>런타임 에러 로그:</b> ${res.stderr}</div>
                            <div style="background:#eff6ff; color:#1e40af; padding:10px; border-radius:4px; font-size:13px; border-left:3px solid #3b82f6;">${recommendation}</div>
                        </div>
                    `;
                }
            });
        } else {
            htmlReport += `<div style="background:#f0fdf4; border:1px solid #bbf7d0; color:#166534; padding:15px; border-radius:6px; font-weight:bold;">🎉 대단합니다! 타깃 문서 내부의 모든 파이썬 예시 코드가 단 하나의 예외 없이 완벽하게 정상 구동되었습니다!</div>`;
        }

        output.innerHTML = htmlReport;

    } catch(err) {
        output.innerHTML = `<div class="error-box">🚨 샌드박스 연산 크래시: ${err.message}</div>`;
    }
}

initEngine();