const { exec, spawn } = require('node:child_process');
const { writeFile } = require('node:fs/promises');
const { promisify } = require('node:util');

const models = ['llama3.1', 'llama3.2', 'mistral', 'gemma3', 'gpt-4o', 'gpt-4', 'o4-mini', 'o3-mini', 'o4', 'gpt-3.5-turbo', 'o1-mini'];
const ollamaModels = ['llama3.1', 'llama3.2', 'mistral', 'gemma3'];


const execAsync = promisify(exec);
async function runPythonScript(modelName, dir) {
  const command = `python uruchom_testy_syntetyczne.py --model ${modelName} --dir ${dir}`;
  const program = 'python';
  const args = `uruchom_testy_syntetyczne.py --model ${modelName} --dir ${dir}`;
  try {
    if (ollamaModels.includes(modelName)) {
      console.log(`Running Ollama model: ${modelName}`);
      await runOllama(modelName);
    }
    console.log(`Executing command: ${command}`);
    const { stdout, stderr } = await runProgram(program, args.split(' '));
    
    await writeFile(`runs/run____${modelName}__${dir}/ok.json`, JSON.stringify({stdout, stderr}), 'utf8');
  } catch (error) {
    console.error(`Execution error: ${error.message}`);
    try {
      await writeFile(`runs/run____${modelName}__${dir}/error.json`, JSON.stringify({ error: error.message, stack: error.stack }), 'utf8');
    } catch (writeError) {
      console.error(`Error writing to file: ${writeError.message}`);
    }
    return null;
  }
}
async function runOllama(modelName) {
  return new Promise((resolve, reject) => {
    const process = spawn('ollama', ['run', modelName]);

    process.stdin.write('/exit\n'); // Wysyłanie komendy /exit
    process.stdin.end();

    process.on('close', (code) => {
      if (code === 0) {
        resolve();
      } else {
        reject(new Error(`Process exited with code ${code}`));
      }
    });

    process.on('error', (error) => {
      reject(error);
    });
  });
}
async function runProgram(command, args) {
  const process = spawn(command, args);
  let stdout = '';
  let stderr = '';
  
    process.stdout.on('data', (data) => {
      console.log(`   ${data.toString()}`);
      stdout += data.toString();
    });

    process.stderr.on('data', (data) => {
      console.error(`   stderr: ${data.toString()}`);
      stderr += data.toString();
    });

    return new Promise((resolve, reject) => {
      process.on('close', (code) => {
        if (code === 0) {
          resolve({stdout, stderr});
        } else {
          reject(new Error(`Process exited with code ${code}`));
        }
      });

      process.on('error', (error) => {
        reject(error);
      });
    });
}

const RUNS = 3; // Number of runs for each model
(async () => {
  const max = models.length * RUNS;
  let current = 0;
  for (const model of models) {
    for (let i = 1; i <= RUNS; ++i) {
      console.log(`${++current}/${max} Running tests for model: ${model}, iteration: 0${i}`);
      await runPythonScript(model, `0${i}`);
    }
  }
})();

