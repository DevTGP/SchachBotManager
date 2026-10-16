#!/usr/bin/env bash
# Temporary diagnosis of C# bots in the runner image.
set -u
uname -a
grep -m1 'model name' /proc/cpuinfo
printf 'FROM sbm-runner-suite\nRUN apt-get update && apt-get install -y --no-install-recommends strace gdb\n' \
  | docker build -t sbm-debug -
cat > /tmp/inner.sh <<'IN'
#!/bin/sh
INIT='{"type":"init","supported":[1],"game_id":"66f1c2a9e4b0a1b2c3d4e5f6","color":"white","start_fen":"rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1","initial_time_ms":300000,"increment_ms":2000,"startup_ms":10000,"memory_limit_mib":1024,"discipline":"x","opponent_name":"y"}'
TURN='{"type":"turn","v":1,"last_move":null,"fen":"rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1","ply":0,"remaining_ms":300000,"opponent_remaining_ms":300000}'
mkdir -p /tmp/bot /tmp/prog; cp /opt/sbm-suite/csharp/Network/bot.dll /tmp/prog/
grep -v seccomp_policy_file /opt/sbm/sandbox/csharp.cfg > /tmp/noseccomp.cfg
sed 's/log_level: WARNING/log_level: DEBUG/' /opt/sbm/sandbox/csharp.cfg > /tmp/debug.cfg
run() {
  echo "=== $*"
  (echo "$INIT"; sleep 6; echo "$TURN"; sleep 3) | SBM_BOT_DIR=/tmp/bot SBM_PROGRAM_DIR=/tmp/prog timeout 30 "$@" 2>&1 | tail -60
  echo "rc=$?"
}
run nsjail -q --config /opt/sbm/sandbox/csharp.cfg -- /sbm/host /sbm/launch/sbm-launch.dll
run nsjail -q --config /tmp/noseccomp.cfg -- /sbm/host /sbm/launch/sbm-launch.dll
run nsjail --config /tmp/debug.cfg -- /sbm/host /sbm/launch/sbm-launch.dll --versions
echo "=== strace"
(echo "$INIT"; sleep 8; echo "$TURN"; sleep 3) | SBM_BOT_DIR=/tmp/bot SBM_PROGRAM_DIR=/tmp/prog timeout 40 strace -f -o /tmp/st.txt nsjail -q --config /opt/sbm/sandbox/csharp.cfg -- /sbm/host /sbm/launch/sbm-launch.dll
echo "rc=$?"
grep -n 'EPERM\|SIGSEGV\|SIGSYS\|ENOSYS\|killed' /tmp/st.txt | grep -v 'ENOENT' | head -80
echo "--- around SIGSEGV"
n=$(grep -n -m1 SIGSEGV /tmp/st.txt | cut -d: -f1)
[ -n "$n" ] && p=$(sed -n "${n}p" /tmp/st.txt | cut -d' ' -f1) && grep "^$p " /tmp/st.txt | tail -60
IN
chmod +x /tmp/inner.sh
docker run --rm -i --tmpfs /tmp:exec \
  --cap-drop ALL --cap-add SYS_ADMIN --cap-add SETUID --cap-add SETGID --cap-add SYS_PTRACE \
  --security-opt seccomp=unconfined --security-opt apparmor=unconfined \
  --cgroupns private --network none -v /tmp/inner.sh:/inner.sh:ro \
  sbm-debug /inner.sh
