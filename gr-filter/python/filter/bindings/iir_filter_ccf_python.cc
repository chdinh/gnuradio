/*
 * Copyright 2020 Free Software Foundation, Inc.
 *
 * This file is part of GNU Radio
 *
 * SPDX-License-Identifier: GPL-3.0-or-later
 *
 */

/* This file is automatically generated using bindtool */

#include <pybind11/pybind11.h>
#include <pybind11/complex.h>
#include <pybind11/stl.h>

namespace py = pybind11;

#include <gnuradio/filter/iir_filter_ccf.h>

void bind_iir_filter_ccf(py::module& m)
{
    using iir_filter_ccf    = gr::filter::iir_filter_ccf;


    py::class_<iir_filter_ccf,gr::sync_block,
        std::shared_ptr<iir_filter_ccf>>(m, "iir_filter_ccf")

        .def(py::init(&iir_filter_ccf::make),
           py::arg("fftaps"), 
           py::arg("fbtaps"), 
           py::arg("oldstyle") = true 
        )
        

        .def("set_taps",&iir_filter_ccf::set_taps,
            py::arg("fftaps"), 
            py::arg("fbtaps") 
        )
        .def("to_basic_block",[](std::shared_ptr<iir_filter_ccf> p){
            return p->to_basic_block();
        })
        ;


} 
