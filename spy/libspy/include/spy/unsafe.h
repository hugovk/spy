#ifndef SPY_UNSAFE_H
#define SPY_UNSAFE_H

#include "spy.h"

spy_GcRef
WASM_EXPORT(spy_gc_alloc_mem)(size_t size);

/* Define the struct and accessor functions to represent a managed pointer to
   type T.

   DEFINE_PTR_TYPE(MyPtr, T) expands to:

   typedef struct { ... } MyPtr;
   static inline MyPtr MyPtr_gc_alloc(...);
   static inline T MyPtr_load(...);
   static inline void MyPtr_store(...);
*/
#define _DEFINE_PTR_TYPE_UNCHECKED(PTR, T)                       \
    typedef struct {                                             \
        T *p;                                                    \
    } PTR;                                                       \
    static inline PTR PTR##_gc_alloc(size_t n) {                 \
        spy_GcRef ref = spy_GcAlloc(sizeof(T) * n);              \
        return ( PTR ){ ref.p };                                 \
    }                                                            \
    static inline T PTR##_load(PTR p, size_t i) {                \
        return p.p[i];                                           \
    }                                                            \
    static inline void PTR##_store(PTR p, size_t i, T v) {       \
        p.p[i] = v;                                              \
    }

#define _DEFINE_PTR_TYPE_CHECKED(PTR, T)                         \
    typedef struct {                                             \
        T *p;                                                    \
        size_t length;                                           \
    } PTR;                                                       \
    static inline PTR PTR##_gc_alloc(size_t n) {                 \
        spy_GcRef ref = spy_GcAlloc(sizeof(T) * n);              \
        return ( PTR ){ ref.p, n };                              \
    }                                                            \
    static inline T PTR##_load(PTR p, size_t i) {                \
        if (i >= p.length)                                       \
            spy_panic("ptr_load out of bounds");                 \
        return p.p[i];                                           \
    }                                                            \
    static inline void PTR##_store(PTR p, size_t i, T v) {       \
        if (i >= p.length)                                       \
            spy_panic("ptr_store ouf of bounds");                \
        p.p[i] = v;                                              \
    }


// XXX this should be configurable
#define SPY_CHECK_PTR

#ifdef SPY_CHECK_PTR
#  define DEFINE_PTR_TYPE _DEFINE_PTR_TYPE_CHECKED
#else
#  define DEFINE_PTR_TYPE _DEFINE_PTR_TYPE_UNCHECKED
#endif

#endif /* SPY_UNSAFE_H */
