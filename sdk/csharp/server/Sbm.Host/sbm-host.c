// The native host every C# program in the sandbox starts through (E205): `sbm-host APP.dll ARGS...`
// runs the framework-dependent .NET app APP.dll with ARGS.
//
// The jail has no /proc. CoreCLR asks glibc for the stack bounds of the thread that starts it, and
// for the main thread glibc reads them from /proc/self/maps; for any other thread it knows them
// itself. So the host starts .NET on a second thread instead of the main thread like `dotnet` does.

#include <dirent.h>
#include <dlfcn.h>
#include <limits.h>
#include <pthread.h>
#include <stdio.h>
#include <string.h>

#define DOTNET_ROOT "/usr/share/dotnet"
#define FXR_DIR DOTNET_ROOT "/host/fxr"
#define STACK_SIZE (8u << 20)

typedef int (*main_startupinfo_fn)(
    int argc, const char** argv, const char* host_path, const char* dotnet_root,
    const char* app_path);

struct start {
    int argc;
    const char** argv;
    const char* app;
    int status;
};

// The image holds exactly one runtime, so the first version directory is the one.
static int find_hostfxr(char* path, size_t size) {
    DIR* dir = opendir(FXR_DIR);
    if (dir == NULL) {
        return -1;
    }
    int found = -1;
    for (struct dirent* entry = readdir(dir); entry != NULL; entry = readdir(dir)) {
        if (entry->d_name[0] != '.') {
            int n = snprintf(path, size, "%s/%s/libhostfxr.so", FXR_DIR, entry->d_name);
            found = n > 0 && (size_t)n < size ? 0 : -1;
            break;
        }
    }
    closedir(dir);
    return found;
}

static void* run(void* arg) {
    struct start* start = arg;
    char path[PATH_MAX];
    if (find_hostfxr(path, sizeof path) != 0) {
        fprintf(stderr, "sbm-host: no hostfxr under %s\n", FXR_DIR);
        return NULL;
    }
    void* fxr = dlopen(path, RTLD_NOW | RTLD_LOCAL);
    if (fxr == NULL) {
        fprintf(stderr, "sbm-host: %s\n", dlerror());
        return NULL;
    }
    // POSIX allows the conversion from the object pointer dlsym returns; ISO C does not.
    main_startupinfo_fn main_startupinfo;
    *(void**)&main_startupinfo = dlsym(fxr, "hostfxr_main_startupinfo");
    if (main_startupinfo == NULL) {
        fprintf(stderr, "sbm-host: %s\n", dlerror());
        return NULL;
    }
    start->status =
        main_startupinfo(start->argc, start->argv, DOTNET_ROOT "/dotnet", DOTNET_ROOT, start->app);
    return NULL;
}

int main(int argc, char** argv) {
    if (argc < 2) {
        fprintf(stderr, "usage: sbm-host APP.dll [ARGS...]\n");
        return 2;
    }
    // hostfxr takes argv[1...] as the arguments of the app, so the app path is taken out.
    struct start start = {argc - 1, (const char**)argv + 1, argv[1], 1};
    argv[1] = argv[0];

    pthread_attr_t attr;
    pthread_t thread;
    if (pthread_attr_init(&attr) != 0 || pthread_attr_setstacksize(&attr, STACK_SIZE) != 0 ||
        pthread_create(&thread, &attr, run, &start) != 0) {
        fprintf(stderr, "sbm-host: cannot start the runtime thread\n");
        return 1;
    }
    pthread_join(thread, NULL);
    return start.status;
}
