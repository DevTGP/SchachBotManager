/* Symbol visibility and C linkage for the core's C interface. */
#ifndef SBM_EXPORT_H
#define SBM_EXPORT_H

#if defined(SBM_STATIC)
#define SBM_API
#elif defined(_WIN32)
#if defined(SBM_BUILD)
#define SBM_API __declspec(dllexport)
#else
#define SBM_API __declspec(dllimport)
#endif
#else
#define SBM_API __attribute__((visibility("default")))
#endif

#ifdef __cplusplus
#define SBM_BEGIN_DECLS extern "C" {
#define SBM_END_DECLS }
#else
#define SBM_BEGIN_DECLS
#define SBM_END_DECLS
#endif

#endif
